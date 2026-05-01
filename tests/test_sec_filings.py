from __future__ import annotations

import unittest
from pathlib import Path

from stockanalysis.ingest.sec.sql import render_sec_filings_upsert_sql
from stockanalysis.ingest.sec.submissions import load_sec_filings_sync_result
from stockanalysis.ingest.sec.upsert import run_sec_filings_upsert


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeExecutor:
    def __init__(self, *, run_id: int = 201, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        return str(self.run_id)

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_upsert and "insert into ingest.source_document" in sql:
            raise RuntimeError("boom")


class SecFilingsTests(unittest.TestCase):
    def test_load_sec_filings_sync_result_from_fixture(self) -> None:
        result = load_sec_filings_sync_result(
            "320193",
            config=type("Config", (), {})(),
            submissions_json_path=str(FIXTURES_DIR / "sec_submissions_CIK0000320193.json"),
        )
        self.assertEqual(result.cik, "0000320193")
        self.assertEqual(result.company_name, "Apple Inc.")
        self.assertEqual(len(result.filings), 2)
        self.assertEqual(result.filings[0].form_type, "10-K")
        self.assertIn("/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm", result.filings[0].filing_url)

    def test_render_sec_filings_upsert_sql(self) -> None:
        result = load_sec_filings_sync_result(
            "320193",
            config=type("Config", (), {})(),
            submissions_json_path=str(FIXTURES_DIR / "sec_submissions_CIK0000320193.json"),
        )
        sql = render_sec_filings_upsert_sql(result, ingested_by_run_id=501)
        self.assertIn("insert into ingest.source_document", sql)
        self.assertIn("sec_edgar", sql)
        self.assertIn("0000320193-24-000123", sql)
        self.assertIn("501::bigint", sql)

    def test_run_sec_filings_upsert_records_pipeline_run_and_ingested_by_run_id(self) -> None:
        executor = FakeExecutor(run_id=77)
        summary = run_sec_filings_upsert(
            "320193",
            config=type("Config", (), {})(),
            submissions_json_path=str(FIXTURES_DIR / "sec_submissions_CIK0000320193.json"),
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 77)
        self.assertEqual(summary["filing_count"], 2)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("77::bigint", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_sec_filings_upsert_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=78, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_sec_filings_upsert(
                "320193",
                config=type("Config", (), {})(),
                submissions_json_path=str(FIXTURES_DIR / "sec_submissions_CIK0000320193.json"),
                executor=executor,
            )
        self.assertEqual(len(executor.non_query_sql), 2)
        self.assertIn("status = 'failed'", executor.non_query_sql[1])
