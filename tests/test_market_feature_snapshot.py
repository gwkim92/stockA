from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.signal.features import (
    compute_market_feature_values,
    load_market_feature_inputs,
    render_feature_definition_upsert_sql,
    render_instrument_feature_upsert_sql,
    render_market_feature_input_lookup_sql,
    run_market_feature_snapshot,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 951, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from price_rows" in sql:
            return json.dumps(
                [
                    {
                        "universe_batch_id": 1001,
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "rank_position": 1,
                        "price_history": [
                            {"trade_date": "2024-10-31", "adjusted_close": "225.9100"},
                            {"trade_date": "2024-11-01", "adjusted_close": "222.9100"},
                        ],
                    },
                    {
                        "universe_batch_id": 1001,
                        "instrument_id": 601,
                        "primary_symbol": "BABA",
                        "rank_position": 2,
                        "price_history": [
                            {"trade_date": "2024-10-31", "adjusted_close": "97.7000"},
                            {"trade_date": "2024-11-01", "adjusted_close": "99.5000"},
                        ],
                    },
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)
        if self.fail_on_upsert and "insert into signal.instrument_feature_value" in sql:
            raise RuntimeError("boom")


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class MarketFeatureSnapshotTests(unittest.TestCase):
    def test_render_market_feature_input_lookup_sql(self) -> None:
        sql = render_market_feature_input_lookup_sql(
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
        )
        self.assertIn("signal.strategy_universe_batch", sql)
        self.assertIn("signal.strategy_universe_member", sql)
        self.assertIn("market.daily_price_bar", sql)
        self.assertIn("fixture-v1", sql)

    def test_load_market_feature_inputs(self) -> None:
        rows = load_market_feature_inputs(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        self.assertEqual([row.primary_symbol for row in rows], ["AAPL", "BABA"])
        self.assertEqual(rows[0].price_history[-1], Decimal("222.9100"))
        self.assertEqual(rows[1].rank_position, 2)

    def test_load_market_feature_inputs_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_market_feature_inputs(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=EmptyExecutor(),
            )

    def test_compute_market_feature_values(self) -> None:
        rows = load_market_feature_inputs(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        feature_rows = compute_market_feature_values(
            rows,
            as_of_date=date(2024, 11, 1),
            feature_set_version="bootstrap-v1",
        )
        self.assertEqual(len(feature_rows), 10)
        by_key = {(row.primary_symbol, row.feature_code): row for row in feature_rows}
        self.assertEqual(by_key[("AAPL", "latest_adjusted_close")].feature_value, Decimal("222.91000000"))
        self.assertEqual(by_key[("AAPL", "return_1d")].feature_value, Decimal("-0.01327962"))
        self.assertEqual(by_key[("BABA", "return_1d")].feature_value, Decimal("0.01842375"))
        self.assertEqual(by_key[("AAPL", "realized_volatility_bootstrap")].feature_value, Decimal("0.01327962"))
        self.assertEqual(by_key[("BABA", "latest_adjusted_close")].zscore, Decimal("-1.00000000"))
        self.assertIsNone(by_key[("AAPL", "observation_count")].zscore)

    def test_render_feature_upsert_sql(self) -> None:
        rows = load_market_feature_inputs(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        feature_rows = compute_market_feature_values(
            rows,
            as_of_date=date(2024, 11, 1),
            feature_set_version="bootstrap-v1",
        )
        definition_sql = render_feature_definition_upsert_sql()
        value_sql = render_instrument_feature_upsert_sql(
            feature_rows,
            as_of_date=date(2024, 11, 1),
            source_run_id=77,
        )
        self.assertIn("insert into signal.feature_definition", definition_sql)
        self.assertIn("latest_adjusted_close", definition_sql)
        self.assertIn("insert into signal.instrument_feature_value", value_sql)
        self.assertIn("77::bigint", value_sql)
        self.assertIn("bootstrap-v1", value_sql)

    def test_run_market_feature_snapshot_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=961)
        summary = run_market_feature_snapshot(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 961)
        self.assertEqual(summary["universe_batch_id"], 1001)
        self.assertEqual(summary["instrument_count"], 2)
        self.assertEqual(summary["feature_definition_count"], 5)
        self.assertEqual(summary["feature_row_count"], 10)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into signal.feature_definition", executor.non_query_sql[0])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[2])

    def test_run_market_feature_snapshot_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=962, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_market_feature_snapshot(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])
