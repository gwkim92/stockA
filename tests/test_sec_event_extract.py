from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from stockanalysis.ingest.sec.event_extract import (
    extract_sec_event_candidate,
    load_pending_sec_event_document_ids,
    load_sec_event_source_document_record,
    run_sec_filings_event_batch_extract,
    run_sec_filings_event_extract,
)
from stockanalysis.ingest.sec.models import SecEventSourceDocumentRecord
from stockanalysis.ingest.sec.sql import render_sec_event_extract_sql


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeExecutor:
    def __init__(self, *, run_id: int = 501, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.pending_ids = ["0000320193-24-000101", "0000320193-24-000123"]
        self.lookup_payload = {
            "document_id": 71,
            "external_document_id": "0000320193-24-000123",
            "title": "10-K - 10-K",
            "summary": "SEC 10-K filing for Apple Inc. | 10-K | file number: 001-36743",
            "published_at": "2024-11-01T00:00:00+00:00",
            "raw_storage_uri": (FIXTURES_DIR / "sec_filing_aapl_20240928_10k.html").resolve().as_uri(),
            "checksum": "abc123",
        }

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "json_agg(external_document_id" in sql:
            return json.dumps(self.pending_ids)
        if "from ingest.source_document" in sql:
            return json.dumps(self.lookup_payload)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_upsert and "insert into event.event" in sql:
            raise RuntimeError("boom")


class SecEventExtractTests(unittest.TestCase):
    def test_load_sec_event_source_document_record(self) -> None:
        record = load_sec_event_source_document_record(
            "0000320193-24-000123",
            executor=FakeExecutor(),
        )
        self.assertEqual(record.document_id, 71)
        self.assertEqual(record.external_document_id, "0000320193-24-000123")
        self.assertEqual(record.summary, "SEC 10-K filing for Apple Inc. | 10-K | file number: 001-36743")

    def test_extract_sec_event_candidate(self) -> None:
        record = SecEventSourceDocumentRecord(
            document_id=71,
            external_document_id="0000320193-24-000123",
            title="10-K - 10-K",
            summary="SEC 10-K filing for Apple Inc. | 10-K | file number: 001-36743",
            published_at=None,
            raw_storage_uri=(FIXTURES_DIR / "sec_filing_aapl_20240928_10k.html").resolve().as_uri(),
            checksum="abc123",
        )
        candidate = extract_sec_event_candidate(record)
        self.assertEqual(candidate.event_type, "sec_annual_report_filed")
        self.assertEqual(candidate.title, "Annual report filed: Apple Inc.")
        self.assertIn("Apple Inc. filed SEC Form 10-K.", candidate.summary)
        self.assertIn("Annual Report", candidate.summary)
        self.assertEqual(candidate.dedupe_key, "sec_edgar:0000320193-24-000123:sec_annual_report_filed")

    def test_render_sec_event_extract_sql(self) -> None:
        record = SecEventSourceDocumentRecord(
            document_id=71,
            external_document_id="0000320193-24-000123",
            title="10-K - 10-K",
            summary="SEC 10-K filing for Apple Inc. | 10-K | file number: 001-36743",
            published_at=None,
            raw_storage_uri=(FIXTURES_DIR / "sec_filing_aapl_20240928_10k.html").resolve().as_uri(),
            checksum="abc123",
        )
        candidate = extract_sec_event_candidate(record)
        sql = render_sec_event_extract_sql(candidate, created_by_run_id=901)
        self.assertIn("insert into event.event", sql)
        self.assertIn("insert into event.event_document_link", sql)
        self.assertIn("sec_annual_report_filed", sql)
        self.assertIn("901::bigint", sql)

    def test_run_sec_filings_event_extract_records_pipeline_run(self) -> None:
        executor = FakeExecutor(run_id=601)
        summary = run_sec_filings_event_extract(
            "0000320193-24-000123",
            config=type("Config", (), {})(),
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 601)
        self.assertEqual(summary["event_type"], "sec_annual_report_filed")
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into event.event", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_sec_filings_event_extract_marks_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=602, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_sec_filings_event_extract(
                "0000320193-24-000123",
                config=type("Config", (), {})(),
                executor=executor,
            )
        self.assertEqual(len(executor.non_query_sql), 2)
        self.assertIn("status = 'failed'", executor.non_query_sql[1])

    def test_load_pending_sec_event_document_ids(self) -> None:
        executor = FakeExecutor()
        pending_ids = load_pending_sec_event_document_ids(limit=5, executor=executor)
        self.assertEqual(pending_ids, ("0000320193-24-000101", "0000320193-24-000123"))
        self.assertIn("limit 5", executor.scalar_sql[0])

    def test_run_sec_filings_event_batch_extract_uses_pending_lookup(self) -> None:
        executor = FakeExecutor(run_id=603)
        summary = run_sec_filings_event_batch_extract(
            config=type("Config", (), {})(),
            limit=10,
            executor=executor,
        )
        self.assertEqual(summary["requested_document_count"], 2)
        self.assertEqual(summary["succeeded_document_count"], 2)
        self.assertEqual(summary["failed_document_count"], 0)
        self.assertEqual(len(summary["results"]), 2)

    def test_run_sec_filings_event_batch_extract_continues_after_failure(self) -> None:
        executor = FakeExecutor(run_id=604)
        with patch(
            "stockanalysis.ingest.sec.event_extract.run_sec_filings_event_extract",
            side_effect=[
                {
                    "run_id": 701,
                    "external_document_id": "0000320193-24-000123",
                    "event_type": "sec_annual_report_filed",
                    "status": "succeeded",
                },
                RuntimeError("boom"),
            ],
        ):
            summary = run_sec_filings_event_batch_extract(
                config=type("Config", (), {})(),
                external_document_ids=["0000320193-24-000123", "0000320193-24-000101"],
                executor=executor,
            )
        self.assertEqual(summary["requested_document_count"], 2)
        self.assertEqual(summary["succeeded_document_count"], 1)
        self.assertEqual(summary["failed_document_count"], 1)
        self.assertEqual(summary["results"][1]["status"], "failed")
