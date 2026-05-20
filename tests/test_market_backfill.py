from __future__ import annotations

import json
import unittest
from datetime import date
from unittest.mock import patch

from stockanalysis.ingest.market.backfill import (
    load_active_universe_symbols,
    render_active_universe_symbol_lookup_sql,
    run_market_price_universe_backfill,
)


class FakeExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "json_build_object" in sql and "from ref.instrument i" in sql:
            return json.dumps(
                [
                    {
                        "symbol": "AAPL",
                        "mic_code": "XNAS",
                        "exchange_name": "NASDAQ",
                    },
                    {
                        "symbol": "BABA",
                        "mic_code": "XNYS",
                        "exchange_name": "New York Stock Exchange",
                    },
                ]
            )
        raise AssertionError(f"Unexpected scalar SQL: {sql}")


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class MarketBackfillTests(unittest.TestCase):
    def test_render_active_universe_symbol_lookup_sql(self) -> None:
        sql = render_active_universe_symbol_lookup_sql(
            mic_codes=("XNAS", "XNYS"),
            limit=5,
        )
        self.assertIn("from ref.instrument i", sql)
        self.assertIn("join ref.exchange e", sql)
        self.assertIn("XNAS", sql)
        self.assertIn("XNYS", sql)
        self.assertIn("limit 5", sql)

    def test_load_active_universe_symbols_uses_exchange_filter(self) -> None:
        executor = FakeExecutor()
        symbols = load_active_universe_symbols(
            config=type("Config", (), {})(),
            exchanges=["Nasdaq", "NYSE"],
            limit=2,
            executor=executor,
        )
        self.assertEqual([symbol.symbol for symbol in symbols], ["AAPL", "BABA"])
        self.assertIn("XNAS", executor.scalar_sql[0])
        self.assertIn("XNYS", executor.scalar_sql[0])
        self.assertIn("limit 2", executor.scalar_sql[0])

    def test_load_active_universe_symbols_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_active_universe_symbols(
                config=type("Config", (), {})(),
                executor=EmptyExecutor(),
            )

    def test_run_market_price_universe_backfill_reuses_batch_runner(self) -> None:
        executor = FakeExecutor()
        with patch("stockanalysis.ingest.market.backfill.run_market_price_batch_upsert") as batch_mock:
            batch_mock.return_value = {
                "requested_symbol_count": 2,
                "succeeded_symbol_count": 2,
                "failed_symbol_count": 0,
                "total_bar_count": 4,
                "results": [],
            }
            summary = run_market_price_universe_backfill(
                config=type("Config", (), {})(),
                exchanges=["Nasdaq", "NYSE"],
                limit=2,
                fixtures_dir="tests/fixtures",
                provider="twelve_data",
                throttle_seconds=1.0,
                max_requests_per_run=3,
                skip_if_fresh=True,
                freshness_date=date(2026, 5, 15),
                executor=executor,
            )
        batch_mock.assert_called_once_with(
            ["AAPL", "BABA"],
            config=unittest.mock.ANY,
            fixtures_dir="tests/fixtures",
            outputsize=None,
            provider="twelve_data",
            throttle_seconds=1.0,
            max_requests_per_run=3,
            skip_if_fresh=True,
            freshness_date=date(2026, 5, 15),
            executor=executor,
        )
        self.assertEqual(summary["selected_symbol_count"], 2)
        self.assertEqual(summary["requested_exchanges"], ["Nasdaq", "NYSE"])
        self.assertEqual(summary["selected_exchange_counts"], {"NASDAQ": 1, "New York Stock Exchange": 1})
        self.assertEqual(summary["total_bar_count"], 4)

    def test_run_market_price_universe_backfill_rejects_unsupported_requested_exchange(self) -> None:
        with self.assertRaises(ValueError):
            run_market_price_universe_backfill(
                config=type("Config", (), {})(),
                exchanges=["OTC"],
                executor=FakeExecutor(),
            )
