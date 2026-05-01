from __future__ import annotations

import unittest
from pathlib import Path

from stockanalysis.ingest.market.universe import (
    load_market_universe_records,
    render_market_universe_bootstrap_sql,
    run_market_universe_bootstrap,
    select_market_universe_records,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeExecutor:
    def __init__(self, *, run_id: int = 701, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_upsert and "insert into ref.issuer" in sql:
            raise RuntimeError("boom")


class MarketUniverseTests(unittest.TestCase):
    def test_load_market_universe_records_from_fixture(self) -> None:
        records = load_market_universe_records(
            config=type("Config", (), {})(),
            company_tickers_json_path=str(FIXTURES_DIR / "sec_company_tickers_exchange_sample.json"),
        )
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0].cik, "0000320193")
        self.assertEqual(records[0].symbol, "AAPL")
        self.assertEqual(records[1].exchange_name, "NYSE")

    def test_select_market_universe_records_filters_supported_exchanges(self) -> None:
        records = load_market_universe_records(
            config=type("Config", (), {})(),
            company_tickers_json_path=str(FIXTURES_DIR / "sec_company_tickers_exchange_sample.json"),
        )
        selection = select_market_universe_records(records)
        self.assertEqual(selection.requested_exchanges, ("Nasdaq", "NYSE"))
        self.assertEqual(len(selection.records), 2)
        self.assertEqual(selection.skipped_unsupported_exchange_count, 1)
        self.assertEqual(selection.records[0].mic_code, "XNAS")
        self.assertEqual(selection.records[1].mic_code, "XNYS")

    def test_render_market_universe_bootstrap_sql(self) -> None:
        records = load_market_universe_records(
            config=type("Config", (), {})(),
            company_tickers_json_path=str(FIXTURES_DIR / "sec_company_tickers_exchange_sample.json"),
        )
        selection = select_market_universe_records(records)
        sql = render_market_universe_bootstrap_sql(selection.records)
        self.assertIn("insert into ref.issuer", sql)
        self.assertIn("insert into ref.instrument", sql)
        self.assertIn("Apple Inc.", sql)
        self.assertIn("Alibaba Group Holding Ltd", sql)
        self.assertIn("XNAS", sql)
        self.assertIn("XNYS", sql)

    def test_run_market_universe_bootstrap_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=811)
        summary = run_market_universe_bootstrap(
            config=type("Config", (), {})(),
            company_tickers_json_path=str(FIXTURES_DIR / "sec_company_tickers_exchange_sample.json"),
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 811)
        self.assertEqual(summary["total_record_count"], 3)
        self.assertEqual(summary["selected_record_count"], 2)
        self.assertEqual(summary["selected_exchange_counts"], {"NYSE": 1, "Nasdaq": 1})
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[0])
        self.assertIn("insert into ref.issuer", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_market_universe_bootstrap_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=812, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_market_universe_bootstrap(
                config=type("Config", (), {})(),
                company_tickers_json_path=str(FIXTURES_DIR / "sec_company_tickers_exchange_sample.json"),
                executor=executor,
            )
        self.assertEqual(len(executor.non_query_sql), 2)
        self.assertIn("status = 'failed'", executor.non_query_sql[1])

    def test_select_market_universe_records_rejects_unsupported_requested_exchange(self) -> None:
        records = load_market_universe_records(
            config=type("Config", (), {})(),
            company_tickers_json_path=str(FIXTURES_DIR / "sec_company_tickers_exchange_sample.json"),
        )
        with self.assertRaises(ValueError):
            select_market_universe_records(records, exchanges=["OTC"])
