from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stockanalysis.ingest.sec.raw_fetch import load_sec_source_document_record, run_sec_filing_raw_fetch


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeExecutor:
    def __init__(
        self,
        *,
        run_id: int = 301,
        fail_on_update: bool = False,
        raw_storage_uri: str | None = None,
        checksum: str | None = None,
    ) -> None:
        self.run_id = run_id
        self.fail_on_update = fail_on_update
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.lookup_payload = {
            "document_id": 71,
            "external_document_id": "0000320193-24-000123",
            "title": "10-K - 10-K",
            "url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
            "raw_storage_uri": raw_storage_uri,
            "checksum": checksum,
        }

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from ingest.source_document" in sql:
            return json.dumps(self.lookup_payload)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_update and "update ingest.source_document" in sql:
            raise RuntimeError("boom")


class SecRawFetchTests(unittest.TestCase):
    def test_load_sec_source_document_record(self) -> None:
        record = load_sec_source_document_record(
            "0000320193-24-000123",
            executor=FakeExecutor(),
        )
        self.assertEqual(record.document_id, 71)
        self.assertEqual(record.external_document_id, "0000320193-24-000123")
        self.assertTrue(record.url.endswith("aapl-20240928.htm"))

    def test_run_sec_filing_raw_fetch_writes_artifact_and_updates_db(self) -> None:
        executor = FakeExecutor(run_id=401)
        with tempfile.TemporaryDirectory() as tmpdir:
            summary = run_sec_filing_raw_fetch(
                "0000320193-24-000123",
                config=type("Config", (), {"resolve": lambda self, name, required: "agent@example.com"})(),
                artifact_root=tmpdir,
                body_path=str(FIXTURES_DIR / "sec_filing_aapl_20240928_10k.html"),
                executor=executor,
            )

            self.assertEqual(summary["run_id"], 401)
            self.assertEqual(summary["status"], "succeeded")
            self.assertIsNotNone(summary["artifact_path"])
            self.assertTrue(Path(summary["artifact_path"]).exists())
            self.assertEqual(len(summary["checksum"]), 64)
            self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
            self.assertIn("update ingest.source_document", executor.non_query_sql[0])
            self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_sec_filing_raw_fetch_skips_existing_artifact_without_force(self) -> None:
        executor = FakeExecutor(
            raw_storage_uri="file:///tmp/sec/filings/0000320193-24-000123/aapl-20240928.htm",
            checksum="abc123",
        )
        summary = run_sec_filing_raw_fetch(
            "0000320193-24-000123",
            config=type("Config", (), {"resolve": lambda self, name, required: "agent@example.com"})(),
            body_path=str(FIXTURES_DIR / "sec_filing_aapl_20240928_10k.html"),
            executor=executor,
        )
        self.assertEqual(summary["status"], "skipped")
        self.assertIsNone(summary["run_id"])
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertEqual(executor.non_query_sql, [])

    def test_run_sec_filing_raw_fetch_marks_pipeline_run_failed_when_update_errors(self) -> None:
        executor = FakeExecutor(run_id=402, fail_on_update=True)
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(RuntimeError):
                run_sec_filing_raw_fetch(
                    "0000320193-24-000123",
                    config=type("Config", (), {"resolve": lambda self, name, required: "agent@example.com"})(),
                    artifact_root=tmpdir,
                    body_path=str(FIXTURES_DIR / "sec_filing_aapl_20240928_10k.html"),
                    executor=executor,
                )
        self.assertEqual(len(executor.non_query_sql), 2)
        self.assertIn("status = 'failed'", executor.non_query_sql[1])
