from __future__ import annotations

import json
import unittest
from pathlib import Path

from stockanalysis.ingest.psql import PsqlExecutionError
from stockanalysis.ingest.sec.companyfacts import load_sec_companyfacts_sync_result, run_sec_companyfacts_upsert
from stockanalysis.ingest.sec.sql import render_sec_companyfacts_upsert_sql


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeExecutor:
    def __init__(self, *, run_id: int = 301, fail_on_upsert: bool = False, missing_instrument: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.missing_instrument = missing_instrument
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.instrument_payload = {
            "instrument_id": 501,
            "primary_symbol": "AAPL",
            "instrument_name": "Apple Inc. Common Stock",
            "issuer_display_name": "Apple Inc.",
            "issuer_legal_name": "Apple Inc.",
        }

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from ref.instrument i" in sql:
            if self.missing_instrument:
                raise PsqlExecutionError("no rows")
            return json.dumps(self.instrument_payload)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_upsert and "insert into market.financial_statement_period" in sql:
            raise RuntimeError("boom")


class SecCompanyFactsTests(unittest.TestCase):
    def test_load_sec_companyfacts_sync_result_from_fixture(self) -> None:
        result = load_sec_companyfacts_sync_result(
            "320193",
            config=type("Config", (), {})(),
            companyfacts_json_path=str(FIXTURES_DIR / "sec_companyfacts_CIK0000320193.json"),
        )
        self.assertEqual(result.cik, "0000320193")
        self.assertEqual(result.company_name, "Apple Inc.")
        self.assertEqual(len(result.values), 5)
        self.assertEqual(result.summary()["period_count"], 2)
        self.assertEqual(result.summary()["metric_codes"], ["net_income", "revenue", "total_assets"])
        self.assertEqual(result.skipped_count, 0)

    def test_render_sec_companyfacts_upsert_sql(self) -> None:
        result = load_sec_companyfacts_sync_result(
            "320193",
            config=type("Config", (), {})(),
            companyfacts_json_path=str(FIXTURES_DIR / "sec_companyfacts_CIK0000320193.json"),
        )
        sql = render_sec_companyfacts_upsert_sql(
            result,
            instrument_id=501,
            source_run_id=901,
        )
        self.assertIn("insert into market.financial_statement_period", sql)
        self.assertIn("insert into market.financial_metric_value", sql)
        self.assertIn("source_periods as", sql)
        self.assertIn("min(r.period_start)::date as period_start", sql)
        self.assertIn("source_metrics as", sql)
        self.assertIn("select distinct on (p.period_id, r.metric_code)", sql)
        self.assertIn("0000320193-24-000123", sql)
        self.assertIn("901::bigint", sql)

    def test_run_sec_companyfacts_upsert_records_pipeline_run_and_source_run_id(self) -> None:
        executor = FakeExecutor(run_id=77)
        summary = run_sec_companyfacts_upsert(
            "320193",
            config=type("Config", (), {})(),
            companyfacts_json_path=str(FIXTURES_DIR / "sec_companyfacts_CIK0000320193.json"),
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 77)
        self.assertEqual(summary["fact_count"], 5)
        self.assertEqual(summary["instrument_symbol"], "AAPL")
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("77::bigint", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_sec_companyfacts_upsert_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=78, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_sec_companyfacts_upsert(
                "320193",
                config=type("Config", (), {})(),
                companyfacts_json_path=str(FIXTURES_DIR / "sec_companyfacts_CIK0000320193.json"),
                executor=executor,
            )
        self.assertEqual(len(executor.non_query_sql), 2)
        self.assertIn("status = 'failed'", executor.non_query_sql[1])

    def test_run_sec_companyfacts_upsert_fails_when_instrument_missing(self) -> None:
        executor = FakeExecutor(run_id=79, missing_instrument=True)
        with self.assertRaises(ValueError):
            run_sec_companyfacts_upsert(
                "320193",
                config=type("Config", (), {})(),
                companyfacts_json_path=str(FIXTURES_DIR / "sec_companyfacts_CIK0000320193.json"),
                executor=executor,
            )
