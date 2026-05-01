from __future__ import annotations

import json
import unittest
from pathlib import Path

from stockanalysis.ingest.market.price import (
    load_market_price_sync_result,
    render_instrument_lookup_by_symbol_sql,
    render_market_price_upsert_sql,
    run_market_price_batch_upsert,
    run_market_price_upsert,
)
from stockanalysis.ingest.psql import PsqlExecutionError


FIXTURES_DIR = Path(__file__).parent / "fixtures"


class FakeExecutor:
    def __init__(
        self,
        *,
        run_id: int = 401,
        run_ids: list[int] | None = None,
        fail_on_upsert: bool = False,
        fail_on_upsert_calls: set[int] | None = None,
        missing_instrument: bool = False,
    ) -> None:
        self.run_id = run_id
        self.run_ids = list(run_ids) if run_ids is not None else None
        self.fail_on_upsert = fail_on_upsert
        self.fail_on_upsert_calls = set(fail_on_upsert_calls or set())
        self.missing_instrument = missing_instrument
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.instrument_payload = {
            "instrument_id": 501,
            "primary_symbol": "AAPL",
            "instrument_name": "Apple Inc. Common Stock",
        }
        self._upsert_call_count = 0

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from ref.instrument i" in sql:
            if self.missing_instrument:
                raise PsqlExecutionError("no rows")
            if "MSFT" in sql:
                return json.dumps(
                    {
                        "instrument_id": 601,
                        "primary_symbol": "MSFT",
                        "instrument_name": "Microsoft Corporation Common Stock",
                    }
                )
            return json.dumps(self.instrument_payload)
        if "insert into ops.pipeline_run" in sql:
            if self.run_ids is not None:
                if not self.run_ids:
                    raise RuntimeError("no remaining run ids")
                return str(self.run_ids.pop(0))
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if "insert into market.daily_price_bar" in sql:
            self._upsert_call_count += 1
        if self.fail_on_upsert and "insert into market.daily_price_bar" in sql:
            raise RuntimeError("boom")
        if self._upsert_call_count in self.fail_on_upsert_calls and "insert into market.daily_price_bar" in sql:
            raise RuntimeError("boom")


class MarketPriceTests(unittest.TestCase):
    def test_load_market_price_sync_result_from_fixture(self) -> None:
        result = load_market_price_sync_result(
            "AAPL",
            config=type("Config", (), {})(),
            prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
        )
        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(len(result.bars), 2)
        self.assertEqual(result.bars[0].trade_date.isoformat(), "2024-10-31")
        self.assertEqual(result.bars[1].adjusted_close, result.bars[1].close)

    def test_render_instrument_lookup_by_symbol_sql(self) -> None:
        sql = render_instrument_lookup_by_symbol_sql("AAPL")
        self.assertIn("from ref.instrument i", sql)
        self.assertIn("AAPL", sql)

    def test_render_market_price_upsert_sql(self) -> None:
        result = load_market_price_sync_result(
            "AAPL",
            config=type("Config", (), {})(),
            prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
        )
        sql = render_market_price_upsert_sql(result, instrument_id=501, source_run_id=901)
        self.assertIn("insert into market.daily_price_bar", sql)
        self.assertIn("501", sql)
        self.assertIn("901::bigint", sql)
        self.assertIn("2024-11-01", sql)

    def test_run_market_price_upsert_records_pipeline_run_and_source_run_id(self) -> None:
        executor = FakeExecutor(run_id=77)
        summary = run_market_price_upsert(
            "AAPL",
            config=type("Config", (), {})(),
            prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 77)
        self.assertEqual(summary["bar_count"], 2)
        self.assertEqual(summary["instrument_symbol"], "AAPL")
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("77::bigint", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[1])

    def test_run_market_price_upsert_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=78, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_market_price_upsert(
                "AAPL",
                config=type("Config", (), {})(),
                prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
                executor=executor,
            )
        self.assertEqual(len(executor.non_query_sql), 2)
        self.assertIn("status = 'failed'", executor.non_query_sql[1])

    def test_run_market_price_upsert_fails_when_instrument_missing(self) -> None:
        executor = FakeExecutor(run_id=79, missing_instrument=True)
        with self.assertRaises(ValueError):
            run_market_price_upsert(
                "AAPL",
                config=type("Config", (), {})(),
                prices_json_path=str(FIXTURES_DIR / "alpha_vantage_daily_adjusted_AAPL.json"),
                executor=executor,
            )

    def test_run_market_price_batch_upsert_uses_fixture_directory(self) -> None:
        executor = FakeExecutor(run_ids=[301, 302])
        summary = run_market_price_batch_upsert(
            ["AAPL", "MSFT"],
            config=type("Config", (), {})(),
            fixtures_dir=str(FIXTURES_DIR),
            executor=executor,
        )
        self.assertEqual(summary["requested_symbol_count"], 2)
        self.assertEqual(summary["succeeded_symbol_count"], 2)
        self.assertEqual(summary["failed_symbol_count"], 0)
        self.assertEqual(summary["total_bar_count"], 4)
        self.assertEqual(summary["results"][0]["run_id"], 301)
        self.assertEqual(summary["results"][1]["run_id"], 302)

    def test_run_market_price_batch_upsert_continues_after_failure(self) -> None:
        executor = FakeExecutor(run_ids=[401, 402], fail_on_upsert_calls={2})
        summary = run_market_price_batch_upsert(
            ["AAPL", "MSFT"],
            config=type("Config", (), {})(),
            fixtures_dir=str(FIXTURES_DIR),
            executor=executor,
        )
        self.assertEqual(summary["requested_symbol_count"], 2)
        self.assertEqual(summary["succeeded_symbol_count"], 1)
        self.assertEqual(summary["failed_symbol_count"], 1)
        self.assertEqual(summary["results"][0]["status"], "succeeded")
        self.assertEqual(summary["results"][1]["status"], "failed")
