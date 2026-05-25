from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.recommendation_quality_eval import (
    DEFAULT_EVAL_NAME,
    parse_horizon_days,
    render_recommendation_quality_eval_insert_sql,
    render_recommendation_quality_eval_sql,
    run_recommendation_quality_eval,
    score_recommendation_quality_eval_payload,
)


class FakeRecommendationQualityExecutor:
    def __init__(self, *, run_id: int = 9401, eval_run_id: int = 501) -> None:
        self.run_id = run_id
        self.eval_run_id = eval_run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- recommendation quality eval lookup"):
            return json.dumps(_payload())
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into ai.eval_run" in sql:
            return str(self.eval_run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql[:120]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class RecommendationQualityEvalTests(unittest.TestCase):
    def test_parse_horizon_days_accepts_d_suffix(self) -> None:
        self.assertEqual(parse_horizon_days("30d"), 30)
        self.assertEqual(parse_horizon_days("90days"), 90)
        self.assertEqual(parse_horizon_days(180), 180)
        with self.assertRaises(ValueError):
            parse_horizon_days("0d")

    def test_render_lookup_sql_is_read_only_and_uses_component_tables(self) -> None:
        sql = render_recommendation_quality_eval_sql(as_of_date=date(2026, 5, 24), horizon_days=30)
        lowered = sql.lower()

        self.assertIn("-- recommendation quality eval lookup", sql)
        self.assertIn("'2026-05-24'::date", sql)
        self.assertIn("signal.recommendation_score_component", sql)
        self.assertIn("performance.recommendation_outcome", sql)
        self.assertIn("trading.paper_validation_run", sql)
        self.assertIn("'macro_regime_score'", sql)
        self.assertIn("'cycle_conflict_penalty'", sql)
        self.assertIn("'fundamental_quality_score'", sql)
        self.assertIn("'valuation_margin_score'", sql)
        self.assertIn("'peer_relative_score'", sql)
        self.assertIn("fundamental_guardrail as", sql)
        self.assertIn("professional_coverage_rows as", sql)
        self.assertIn("market.financial_metric_normalized", sql)
        self.assertIn("market.peer_relative_snapshot", sql)
        self.assertIn("market.valuation_snapshot", sql)
        self.assertIn("research.industry_competitive_position", sql)
        self.assertIn("research.equity_research_artifact", sql)
        self.assertIn("select distinct on (primary_symbol)", sql)
        self.assertIn("'professional_analysis_coverage'", sql)
        self.assertNotIn("'macro_flow_score'", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_score_payload_marks_sufficient_sample_without_mutating_weights(self) -> None:
        score = score_recommendation_quality_eval_payload(_payload(), min_sample_size=2)

        self.assertEqual(score["quality_status"], "ready_for_weight_review")
        self.assertEqual(score["sample_status"], "sufficient_sample")
        self.assertEqual(score["recommendation_count"], 3)
        self.assertEqual(score["outcome_count"], 2)
        self.assertEqual(score["outcome_coverage_rate"], 0.666667)
        self.assertTrue(score["cycle_weight_guardrail"]["cycle_weight_unchanged"])
        self.assertTrue(score["fundamental_weight_guardrail"]["fundamental_weight_unchanged"])
        self.assertFalse(score["cycle_weight_guardrail"]["recommendation_scoring_mutated"])
        self.assertFalse(score["fundamental_weight_guardrail"]["recommendation_scoring_mutated"])
        self.assertEqual(score["professional_analysis_coverage"]["status"], "sufficient_coverage")
        self.assertEqual(score["professional_analysis_coverage"]["complete_professional_coverage_rate"], 1.0)
        self.assertEqual(
            score["professional_analysis_coverage"]["layer_coverage"]["valuation_snapshot"]["coverage_rate"],
            1.0,
        )
        self.assertEqual(score["paper_validation"]["latest_status"], "passed")
        self.assertEqual(score["component_metrics"][0]["component_name"], "cycle_score")

    def test_score_payload_blocks_weight_review_when_fundamental_weight_changed(self) -> None:
        payload = _payload()
        payload["fundamental_weight_guardrail"] = {
            "fundamental_component_row_count": 5,
            "zero_weight_fundamental_component_row_count": 4,
            "observed_fundamental_component_count": 5,
        }

        score = score_recommendation_quality_eval_payload(payload, min_sample_size=2)

        self.assertEqual(score["quality_status"], "needs_more_data")
        self.assertFalse(score["fundamental_weight_guardrail"]["fundamental_weight_unchanged"])
        self.assertIn("fundamental/valuation/peer component weight", score["next_action"])

    def test_score_payload_keeps_weight_change_blocked_when_sample_is_small(self) -> None:
        score = score_recommendation_quality_eval_payload(_payload(), min_sample_size=10)

        self.assertEqual(score["quality_status"], "needs_more_data")
        self.assertEqual(score["sample_status"], "insufficient_sample")
        self.assertIn("weight를 변경하지", score["next_action"])

    def test_score_payload_blocks_weight_review_when_professional_coverage_is_insufficient(self) -> None:
        payload = _payload()
        payload["professional_analysis_coverage"] = {
            "recommendation_count": 3,
            "financial_metric_coverage_count": 3,
            "peer_relative_coverage_count": 2,
            "valuation_coverage_count": 2,
            "industry_position_coverage_count": 2,
            "equity_research_coverage_count": 1,
            "thesis_coverage_count": 3,
            "complete_professional_coverage_count": 1,
        }
        payload["professional_analysis_gap_examples"] = [
            {
                "primary_symbol": "ARM",
                "missing_layers": ["equity_research_artifact", "valuation_snapshot"],
            }
        ]

        score = score_recommendation_quality_eval_payload(
            payload,
            min_sample_size=2,
            min_professional_coverage_rate=0.8,
        )

        self.assertEqual(score["quality_status"], "needs_more_data")
        self.assertEqual(score["professional_analysis_coverage"]["status"], "insufficient_coverage")
        self.assertEqual(score["professional_analysis_coverage"]["complete_professional_coverage_rate"], 0.333333)
        self.assertEqual(score["professional_analysis_coverage"]["gap_examples"][0]["symbol"], "ARM")
        self.assertIn("전문가식 분석 coverage", score["next_action"])

    def test_render_eval_insert_sql_uses_ai_eval_run(self) -> None:
        sql = render_recommendation_quality_eval_insert_sql(
            eval_name=DEFAULT_EVAL_NAME,
            dataset_version="recommendation-quality-live-v1",
            provider="postgres",
            model_name="deterministic-sql-v1",
            score_json={"quality_status": "needs_more_data"},
        )

        self.assertIn("insert into ai.eval_run", sql)
        self.assertIn("'recommendation_quality_calibration'", sql)
        self.assertIn("'postgres'", sql)

    def test_run_dry_run_reads_payload_without_writes(self) -> None:
        executor = FakeRecommendationQualityExecutor()

        report = run_recommendation_quality_eval(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 24),
            horizon_days=30,
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["score"]["eval_name"], DEFAULT_EVAL_NAME)
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_execute_records_pipeline_and_eval_run(self) -> None:
        executor = FakeRecommendationQualityExecutor(run_id=9402, eval_run_id=502)

        report = run_recommendation_quality_eval(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 24),
            horizon_days=30,
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9402)
        self.assertEqual(report["eval_run_id"], 502)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


def _payload() -> dict[str, object]:
    return {
        "as_of_date": "2026-05-24",
        "horizon_days": 30,
        "summary": {
            "recommendation_count": 3,
            "outcome_count": 2,
            "positive_outcome_count": 1,
            "avg_absolute_return_pct": "0.02500000",
            "avg_alpha_pct": "0.01000000",
            "avg_max_drawdown_pct": "-0.03000000",
            "first_recommendation_date": "2026-04-24",
            "latest_recommendation_date": "2026-05-20",
        },
        "component_metrics": [
            {
                "component_name": "cycle_score",
                "recommendation_count": 3,
                "outcome_count": 2,
                "avg_component_score": "0.61000000",
                "avg_positive_score": "0.70000000",
                "avg_non_positive_score": "0.52000000",
                "positive_score_spread": "0.18000000",
                "avg_component_weight": "0.45000000",
                "zero_weight_cycle_component_rows": 0,
            },
            {
                "component_name": "macro_regime_score",
                "recommendation_count": 3,
                "outcome_count": 2,
                "avg_component_score": "0.50000000",
                "avg_positive_score": "0.56000000",
                "avg_non_positive_score": "0.44000000",
                "positive_score_spread": "0.12000000",
                "avg_component_weight": "0.00000000",
                "zero_weight_cycle_component_rows": 3,
            },
        ],
        "cycle_weight_guardrail": {
            "cycle_component_row_count": 6,
            "zero_weight_cycle_component_row_count": 6,
            "observed_cycle_component_count": 2,
        },
        "fundamental_weight_guardrail": {
            "fundamental_component_row_count": 10,
            "zero_weight_fundamental_component_row_count": 10,
            "observed_fundamental_component_count": 5,
        },
        "professional_analysis_coverage": {
            "recommendation_count": 3,
            "financial_metric_coverage_count": 3,
            "peer_relative_coverage_count": 3,
            "valuation_coverage_count": 3,
            "industry_position_coverage_count": 3,
            "equity_research_coverage_count": 3,
            "thesis_coverage_count": 3,
            "complete_professional_coverage_count": 3,
        },
        "professional_analysis_gap_examples": [],
        "paper_validation": {
            "paper_validation_run_id": 7,
            "validation_date": "2026-05-24",
            "status": "passed",
            "recommendation_count": 3,
            "conflict_count": 0,
            "approved_action_count": 2,
        },
        "outcome_label_counts": {"positive": 1, "negative": 1},
    }


if __name__ == "__main__":
    unittest.main()
