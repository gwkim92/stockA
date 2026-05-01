from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.signal.thesis_review import (
    ThesisReviewCandidate,
    build_thesis_review_rows,
    load_thesis_review_candidates,
    render_thesis_review_candidate_lookup_sql,
    render_thesis_review_upsert_sql,
    run_thesis_review_bootstrap,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 4001, review_count: int = 1, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.review_count = review_count
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- thesis review candidate lookup"):
            return json.dumps(
                [
                    {
                        "batch_id": 2001,
                        "recommendation_id": 9001,
                        "thesis_id": 7001,
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "thesis_type": "long_term_core",
                        "thesis_title": "AAPL watch thesis via Annual Reporting",
                        "bucket": "watch",
                        "action": "watch",
                        "rank_position": 1,
                        "total_score": "0.3610",
                        "primary_node_id": 11,
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
        if "insert into signal.thesis_review" in sql:
            if self.fail_on_upsert:
                raise RuntimeError("boom")
            return str(self.review_count)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class ThesisReviewBootstrapTests(unittest.TestCase):
    def test_render_thesis_review_candidate_lookup_sql(self) -> None:
        sql = render_thesis_review_candidate_lookup_sql(
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
        )
        self.assertIn("signal.recommendation_batch", sql)
        self.assertIn("signal.recommendation", sql)
        self.assertIn("signal.investment_thesis", sql)
        self.assertIn("signal.cycle_state_snapshot", sql)
        self.assertIn("signal.instrument_feature_value", sql)
        self.assertIn("recommendation.thesis_id is not null", sql)

    def test_load_thesis_review_candidates(self) -> None:
        rows = load_thesis_review_candidates(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].primary_symbol, "AAPL")
        self.assertEqual(rows[0].thesis_id, 7001)
        self.assertEqual(rows[0].cycle_state, "forming")
        self.assertEqual(rows[0].total_score, Decimal("0.3610"))

    def test_load_thesis_review_candidates_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_thesis_review_candidates(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=EmptyExecutor(),
            )

    def test_build_thesis_review_rows_uses_deterministic_rule(self) -> None:
        rows = build_thesis_review_rows(
            (
                _candidate(
                    bucket="watch",
                    action="watch",
                    total_score=Decimal("0.3610"),
                    cycle_state="forming",
                ),
            ),
            review_date=date(2024, 11, 1),
        )
        self.assertEqual(rows[0].action, "watch")
        self.assertEqual(rows[0].health_score, Decimal("0.3610"))
        self.assertEqual(rows[0].next_review_date, date(2024, 12, 1))
        self.assertIn("Recommendation bucket watch score 0.3610", rows[0].summary)

    def test_build_thesis_review_rows_marks_exit_for_broken_cycle(self) -> None:
        rows = build_thesis_review_rows(
            (
                _candidate(
                    bucket="core",
                    action="buy_candidate",
                    total_score=Decimal("0.8200"),
                    cycle_state="structurally_broken",
                ),
            ),
            review_date=date(2024, 11, 1),
        )
        self.assertEqual(rows[0].action, "exit")
        self.assertEqual(rows[0].health_score, Decimal("0.2500"))
        self.assertEqual(rows[0].next_review_date, date(2024, 11, 8))

    def test_render_thesis_review_upsert_sql(self) -> None:
        rows = build_thesis_review_rows((_candidate(),), review_date=date(2024, 11, 1))
        sql = render_thesis_review_upsert_sql(rows, source_run_id=77)
        self.assertIn("insert into signal.thesis_review", sql)
        self.assertIn("on conflict (thesis_id, review_date, review_source) do update", sql)
        self.assertIn("'watch'::text", sql)
        self.assertIn("0.3610::numeric", sql)
        self.assertIn("77::bigint", sql)

    def test_run_thesis_review_bootstrap_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=4002, review_count=1)
        summary = run_thesis_review_bootstrap(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 4002)
        self.assertEqual(summary["batch_id"], 2001)
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["review_count"], 1)
        self.assertEqual(summary["action_counts"], {"watch": 1})
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into signal.thesis_review", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_thesis_review_bootstrap_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=4003, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_thesis_review_bootstrap(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])


def _candidate(
    *,
    bucket: str = "watch",
    action: str = "watch",
    total_score: Decimal = Decimal("0.3610"),
    cycle_state: str | None = "forming",
) -> ThesisReviewCandidate:
    return ThesisReviewCandidate(
        batch_id=2001,
        recommendation_id=9001,
        thesis_id=7001,
        instrument_id=501,
        primary_symbol="AAPL",
        thesis_type="long_term_core",
        thesis_title="AAPL watch thesis via Annual Reporting",
        bucket=bucket,
        action=action,
        rank_position=1,
        total_score=total_score,
        primary_node_id=11,
        node_code="ANNUAL_REPORTING",
        node_name="Annual Reporting",
        cycle_state=cycle_state,
        cycle_score=Decimal("0.2075") if cycle_state is not None else None,
        return_1d=Decimal("-0.01327962"),
        return_since_first=Decimal("-0.01327962"),
        latest_adjusted_close=Decimal("222.91000000"),
    )
