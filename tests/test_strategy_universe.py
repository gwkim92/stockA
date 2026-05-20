from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.signal.universe import (
    load_strategy_universe_candidates,
    render_strategy_universe_candidate_lookup_sql,
    render_strategy_universe_upsert_sql,
    run_strategy_universe_slice,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 901, batch_id: int = 1001, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.batch_id = batch_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if "from ranked_rows r" in sql:
            return json.dumps(
                [
                    {
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "exchange_name": "NASDAQ",
                        "latest_trade_date": "2024-11-01",
                        "latest_adjusted_close": "222.910000",
                        "observation_count": 2,
                        "selection_score": "2.2229",
                        "rank_position": 1,
                    },
                    {
                        "instrument_id": 601,
                        "primary_symbol": "BABA",
                        "exchange_name": "New York Stock Exchange",
                        "latest_trade_date": "2024-11-01",
                        "latest_adjusted_close": "99.500000",
                        "observation_count": 2,
                        "selection_score": "2.0995",
                        "rank_position": 2,
                    },
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into signal.strategy_universe_batch" in sql:
            if self.fail_on_upsert:
                raise RuntimeError("boom")
            return str(self.batch_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class StrategyUniverseTests(unittest.TestCase):
    def test_render_strategy_universe_candidate_lookup_sql(self) -> None:
        sql = render_strategy_universe_candidate_lookup_sql(
            as_of_date=date(2024, 11, 1),
            market_code="US",
            mic_codes=("XNAS", "XNYS"),
            min_observation_count=2,
            min_adjusted_close=Decimal("50"),
            limit=10,
        )
        self.assertIn("market.daily_price_bar", sql)
        self.assertIn("ref.instrument i", sql)
        self.assertIn("XNAS", sql)
        self.assertIn("XNYS", sql)
        self.assertIn("pc.observation_count >= 2", sql)
        self.assertIn("limit 10", sql)

    def test_load_strategy_universe_candidates_from_lookup(self) -> None:
        candidates = load_strategy_universe_candidates(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            min_observation_count=2,
            min_adjusted_close=Decimal("50"),
            executor=FakeExecutor(),
        )
        self.assertEqual([candidate.primary_symbol for candidate in candidates], ["AAPL", "BABA"])
        self.assertEqual(candidates[0].rank_position, 1)
        self.assertEqual(candidates[1].latest_adjusted_close, Decimal("99.500000"))

    def test_load_strategy_universe_candidates_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_strategy_universe_candidates(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                executor=EmptyExecutor(),
            )

    def test_render_strategy_universe_upsert_sql(self) -> None:
        candidates = load_strategy_universe_candidates(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            executor=FakeExecutor(),
        )
        sql = render_strategy_universe_upsert_sql(
            candidates,
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            selection_rule="fixture rule",
            source_run_id=77,
        )
        self.assertIn("insert into signal.strategy_universe_batch", sql)
        self.assertIn("insert into signal.strategy_universe_member", sql)
        self.assertIn("from delete_existing", sql)
        self.assertIn("on conflict (universe_batch_id, instrument_id) do update", sql)
        self.assertIn("fixture-v1", sql)
        self.assertIn("77::bigint", sql)

    def test_run_strategy_universe_slice_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=911, batch_id=1201)
        summary = run_strategy_universe_slice(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            min_observation_count=2,
            min_adjusted_close=Decimal("50"),
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 911)
        self.assertEqual(summary["universe_batch_id"], 1201)
        self.assertEqual(summary["member_count"], 2)
        self.assertEqual(summary["selected_symbol_preview"], ["AAPL", "BABA"])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_strategy_universe_slice_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=912, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_strategy_universe_slice(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=executor,
            )
        self.assertEqual(len(executor.non_query_sql), 1)
        self.assertIn("status = 'failed'", executor.non_query_sql[0])

    def test_run_strategy_universe_slice_rejects_unsupported_requested_exchange(self) -> None:
        with self.assertRaises(ValueError):
            run_strategy_universe_slice(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                exchanges=["OTC"],
                executor=FakeExecutor(),
            )
