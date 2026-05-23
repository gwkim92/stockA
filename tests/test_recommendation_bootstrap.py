from __future__ import annotations

import json
import unittest
from datetime import date
from decimal import Decimal

from stockanalysis.signal.recommendation import (
    RecommendationCandidate,
    compute_recommendation_rows,
    load_recommendation_candidates,
    render_recommendation_candidate_lookup_sql,
    render_recommendation_upsert_sql,
    run_recommendation_bootstrap,
)


class FakeExecutor:
    def __init__(self, *, run_id: int = 1001, batch_id: int = 2001, fail_on_upsert: bool = False) -> None:
        self.run_id = run_id
        self.batch_id = batch_id
        self.fail_on_upsert = fail_on_upsert
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- recommendation candidate lookup"):
            return json.dumps(
                [
                    {
                        "universe_batch_id": 1001,
                        "instrument_id": 501,
                        "primary_symbol": "AAPL",
                        "universe_rank_position": 1,
                        "universe_member_count": 2,
                        "node_id": 11,
                        "node_code": "ANNUAL_REPORTING",
                        "node_name": "Annual Reporting",
                        "cycle_state": "forming",
                        "cycle_score": "0.2075",
                        "return_1d": "-0.01327962",
                        "return_since_first": "-0.01327962",
                        "return_since_first_zscore": "-1.00000000",
                        "latest_adjusted_close": "222.91000000",
                        "macro_flow_score": "0.00000000",
                        "macro_regime_score": "0.51000000",
                        "domain_cycle_score": "0.50000000",
                        "theme_cycle_score": "0.48000000",
                        "instrument_cycle_score": "0.20750000",
                        "cycle_conflict_penalty": "0.80000000",
                    }
                ]
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into signal.recommendation_batch" in sql:
            if self.fail_on_upsert:
                raise RuntimeError("boom")
            return str(self.batch_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class EmptyExecutor:
    def execute_scalar(self, sql: str) -> str:
        return "[]"


class RecommendationBootstrapTests(unittest.TestCase):
    def test_render_recommendation_candidate_lookup_sql(self) -> None:
        sql = render_recommendation_candidate_lookup_sql(
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
        )
        self.assertIn("signal.strategy_universe_batch", sql)
        self.assertIn("ref.instrument_classification_membership", sql)
        self.assertIn("signal.cycle_state_snapshot", sql)
        self.assertIn("signal.cycle_hierarchy_state_snapshot", sql)
        self.assertIn("macro_regime_score", sql)
        self.assertIn("domain_cycle_score", sql)
        self.assertIn("theme_cycle_score", sql)
        self.assertIn("cycle_conflict_penalty", sql)
        self.assertIn("signal.instrument_feature_value", sql)
        self.assertIn("signal.propagated_instrument_impact", sql)
        self.assertIn("return_since_first_observation", sql)

    def test_load_recommendation_candidates(self) -> None:
        rows = load_recommendation_candidates(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=FakeExecutor(),
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].primary_symbol, "AAPL")
        self.assertEqual(rows[0].node_code, "ANNUAL_REPORTING")
        self.assertEqual(rows[0].cycle_score, Decimal("0.2075"))
        self.assertEqual(rows[0].macro_regime_score, Decimal("0.51000000"))
        self.assertEqual(rows[0].cycle_conflict_penalty, Decimal("0.80000000"))

    def test_load_recommendation_candidates_fails_when_empty(self) -> None:
        with self.assertRaises(ValueError):
            load_recommendation_candidates(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=EmptyExecutor(),
            )

    def test_compute_recommendation_rows(self) -> None:
        rows = compute_recommendation_rows(
            (
                RecommendationCandidate(
                    universe_batch_id=1001,
                    instrument_id=501,
                    primary_symbol="AAPL",
                    universe_rank_position=1,
                    universe_member_count=2,
                    node_id=11,
                    node_code="ANNUAL_REPORTING",
                    node_name="Annual Reporting",
                    cycle_state="forming",
                    cycle_score=Decimal("0.2075"),
                    return_1d=Decimal("-0.01327962"),
                    return_since_first=Decimal("-0.01327962"),
                    return_since_first_zscore=Decimal("-1.00000000"),
                    latest_adjusted_close=Decimal("222.91000000"),
                    macro_flow_score=Decimal("0.00000000"),
                ),
                RecommendationCandidate(
                    universe_batch_id=1001,
                    instrument_id=701,
                    primary_symbol="NVDA",
                    universe_rank_position=2,
                    universe_member_count=2,
                    node_id=21,
                    node_code="AI_INFRA",
                    node_name="AI Infrastructure",
                    cycle_state="expanding",
                    cycle_score=Decimal("0.8338"),
                    return_1d=Decimal("0.03000000"),
                    return_since_first=Decimal("0.18000000"),
                    return_since_first_zscore=Decimal("1.50000000"),
                    latest_adjusted_close=Decimal("150.00000000"),
                    macro_flow_score=Decimal("0.00000000"),
                ),
            )
        )
        by_symbol = {row.primary_symbol: row for row in rows}
        self.assertEqual(rows[0].primary_symbol, "NVDA")
        self.assertEqual(by_symbol["AAPL"].bucket, "watch")
        self.assertEqual(by_symbol["AAPL"].action, "watch")
        self.assertEqual(by_symbol["AAPL"].total_score, Decimal("0.3610"))
        self.assertEqual(by_symbol["AAPL"].recommended_weight, None)
        self.assertEqual(
            by_symbol["AAPL"].component_scores,
            {
                "cycle_score": "0.2075",
                "macro_regime_score": "0.5000",
                "domain_cycle_score": "0.5000",
                "theme_cycle_score": "0.2075",
                "instrument_cycle_score": "0.2075",
                "cycle_conflict_penalty": "1.0000",
                "momentum_score": "0.2500",
                "short_term_score": "0.3672",
                "rank_score": "1.0000",
                "macro_flow_score": "0.0000",
            },
        )
        self.assertEqual(by_symbol["NVDA"].bucket, "cycle")
        self.assertEqual(by_symbol["NVDA"].recommended_weight, Decimal("0.0400"))

    def test_render_recommendation_upsert_sql(self) -> None:
        rows = compute_recommendation_rows(
            (
                RecommendationCandidate(
                    universe_batch_id=1001,
                    instrument_id=501,
                    primary_symbol="AAPL",
                    universe_rank_position=1,
                    universe_member_count=2,
                    node_id=11,
                    node_code="ANNUAL_REPORTING",
                    node_name="Annual Reporting",
                    cycle_state="forming",
                    cycle_score=Decimal("0.2075"),
                    return_1d=Decimal("-0.01327962"),
                    return_since_first=Decimal("-0.01327962"),
                    return_since_first_zscore=Decimal("-1.00000000"),
                    latest_adjusted_close=Decimal("222.91000000"),
                    macro_flow_score=Decimal("0.00000000"),
                ),
            )
        )
        sql = render_recommendation_upsert_sql(
            rows,
            as_of_date=date(2024, 11, 1),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            score_version="bootstrap-v1",
            source_run_id=77,
        )
        self.assertIn("insert into signal.recommendation_batch", sql)
        self.assertIn("insert into signal.recommendation", sql)
        self.assertIn("returning 1", sql)
        self.assertIn("from delete_existing", sql)
        self.assertIn("insert into signal.recommendation_score_component", sql)
        self.assertIn("source_components", sql)
        self.assertIn("'cycle_score'", sql)
        self.assertIn("0.45::numeric", sql)
        self.assertIn("'macro_regime_score'", sql)
        self.assertIn("'domain_cycle_score'", sql)
        self.assertIn("'theme_cycle_score'", sql)
        self.assertIn("'instrument_cycle_score'", sql)
        self.assertIn("'cycle_conflict_penalty'", sql)
        self.assertIn("0.0000::numeric", sql)
        self.assertIn("'macro_flow_score'", sql)
        self.assertIn("0.10::numeric", sql)
        self.assertIn("'Normalized current cycle state score from the linked internal theme.'", sql)
        self.assertIn("'Latest hierarchical macro-regime cycle score connected to the theme path.'", sql)
        self.assertIn("77::bigint", sql)
        self.assertIn("'watch'", sql)
        self.assertIn("0.3610", sql)

    def test_run_recommendation_bootstrap_records_pipeline_run_and_summary(self) -> None:
        executor = FakeExecutor(run_id=1002, batch_id=2002)
        summary = run_recommendation_bootstrap(
            config=type("Config", (), {})(),
            as_of_date=date(2024, 11, 1),
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="fixture-v1",
            executor=executor,
        )
        self.assertEqual(summary["run_id"], 1002)
        self.assertEqual(summary["batch_id"], 2002)
        self.assertEqual(summary["universe_batch_id"], 1001)
        self.assertEqual(summary["candidate_count"], 1)
        self.assertEqual(summary["recommendation_count"], 1)
        self.assertEqual(summary["score_component_count"], 10)
        self.assertEqual(summary["bucket_counts"], {"watch": 1})
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into signal.recommendation_batch", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_recommendation_bootstrap_marks_pipeline_run_failed_when_upsert_errors(self) -> None:
        executor = FakeExecutor(run_id=1003, fail_on_upsert=True)
        with self.assertRaises(RuntimeError):
            run_recommendation_bootstrap(
                config=type("Config", (), {})(),
                as_of_date=date(2024, 11, 1),
                strategy_name="long_term_core",
                horizon_type="long_term",
                universe_version="fixture-v1",
                executor=executor,
            )
        self.assertIn("status = 'failed'", executor.non_query_sql[-1])
