from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.signal.thesis import (
    ThesisCandidate,
    build_thesis_rows,
    load_thesis_candidates,
    render_thesis_candidate_lookup_sql,
    render_thesis_upsert_sql,
    run_thesis_bootstrap,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 3001, linked_count: int = 1, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.linked_count = linked_count
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- thesis bootstrap candidate lookup"):
            return json.dumps(
                [
                    {
                        "batch_id": 2001,
                        "recommendation_id": 9001,
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "bucket": "watch",
                        "action": "watch",
                        "rank_position": 1,
                        "total_score": "0.3610",
                        "node_id": 11,
                        "node_code": "ANNUAL_REPORTING",
                        "node_name": "Annual Reporting",
                        "cycle_state": "forming",
                        "cycle_score": "0.2075",
                        "return_1d": "-0.01327962",
                        "return_since_first": "-0.01327962",
                        "latest_adjusted_close": "222.91000000",
                    }
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into signal.investment_thesis" in sql:
            if self.fail_on_upsert:
                raise RuntimeError("boom")
            return str(self.linked_count)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class ThesisBootstrapTests(unittest.TestCase):
    def test_render_thesis_candidate_lookup_sql(self) -> None:
        sql = render_thesis_candidate_lookup_sql(
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
        )
        self.assertIn("signal.recommendation_batch", sql)
        self.assertIn("signal.recommendation", sql)
        self.assertIn("ref.instrument_classification_membership", sql)
        self.assertIn("signal.cycle_state_snapshot", sql)
        self.assertIn("return_since_first_observation", sql)
        self.assertIn("recommendation.status = 'active'", sql)

    def test_load_thesis_candidates(self) -> None:
        rows = load_thesis_candidates(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].primary_symbol, "AAPL")
        self.assertEqual(rows[0].node_code, "ANNUAL_REPORTING")
        self.assertEqual(rows[0].total_score, Decimal("0.3610"))

    def test_load_thesis_candidates_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_thesis_candidates(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=EmptyExecutor(),
            )

    def test_build_thesis_rows_uses_deterministic_template(self) -> None:
        rows = build_thesis_rows(
            (
                ThesisCandidate(
                    batch_id=2001,
                    recommendation_id=9001,
                    instrument_id=501,
                    primary_symbol="AAPL",
                    bucket="watch",
                    action="watch",
                    rank_position=1,
                    total_score=Decimal("0.3610"),
                    node_id=11,
                    node_code="ANNUAL_REPORTING",
                    node_name="Annual Reporting",
                    cycle_state="forming",
                    cycle_score=Decimal("0.2075"),
                    return_1d=Decimal("-0.01327962"),
                    return_since_first=Decimal("-0.01327962"),
                    latest_adjusted_close=Decimal("222.91000000"),
                ),
            ),
            strategy_name="long_term_core",
            horizon_type="long_term",
        )
        self.assertEqual(rows[0].title, "AAPL watch thesis via Annual Reporting")
        self.assertEqual(rows[0].thesis_type, "long_term_core")
        self.assertEqual(rows[0].conviction_score, Decimal("0.3610"))
        self.assertEqual(rows[0].expected_holding_days, 365)
        self.assertEqual(rows[0].benchmark_code, "SPY")
        self.assertIn("falls below 0.3500", rows[0].invalidation_conditions)

    def test_render_thesis_upsert_sql_links_recommendation(self) -> None:
        thesis_rows = build_thesis_rows(
            (
                ThesisCandidate(
                    batch_id=2001,
                    recommendation_id=9001,
                    instrument_id=501,
                    primary_symbol="AAPL",
                    bucket="watch",
                    action="watch",
                    rank_position=1,
                    total_score=Decimal("0.3610"),
                    node_id=11,
                    node_code="ANNUAL_REPORTING",
                    node_name="Annual Reporting",
                    cycle_state="forming",
                    cycle_score=Decimal("0.2075"),
                    return_1d=None,
                    return_since_first=None,
                    latest_adjusted_close=None,
                ),
            ),
            strategy_name="long_term_core",
            horizon_type="long_term",
        )
        sql = render_thesis_upsert_sql(thesis_rows, source_run_id=77)
        self.assertIn("insert into signal.investment_thesis", sql)
        self.assertIn("update signal.investment_thesis", sql)
        self.assertIn("update signal.recommendation recommendation", sql)
        self.assertIn("set thesis_id = all_links.thesis_id", sql)
        self.assertIn("'AAPL watch thesis via Annual Reporting'::text", sql)
        self.assertIn("77::bigint", sql)

    def test_run_thesis_bootstrap_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=3002, linked_count=1)
        summary = run_thesis_bootstrap(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 3002)
        self.assertEqual(summary["batch_id"], 2001)
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["thesis_count"], 1)
        self.assertEqual(summary["linked_recommendation_count"], 1)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into signal.investment_thesis", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_thesis_bootstrap_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=3003, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_thesis_bootstrap(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])
