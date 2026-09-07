from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.recommendation_eval_persistence import (
    SNAPSHOT_SCHEMA_VERSION,
    build_recommendation_eval_snapshots,
    canonical_snapshot_json,
)
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

    def test_render_lookup_sql_is_read_only_and_captures_snapshot_source_state(self) -> None:
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
        self.assertIn("'recommendation_snapshots'", sql)
        self.assertIn("'invalidation_conditions'", sql)
        self.assertIn("'entry_conditions'", sql)
        self.assertIn("'exit_conditions'", sql)
        self.assertIn("'score_components'", sql)
        self.assertIn("'explanation'", sql)
        self.assertIn("'selected_outcome'", sql)
        self.assertIn("'outcome_id'", sql)
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
            {"primary_symbol": "ARM", "missing_layers": ["equity_research_artifact", "valuation_snapshot"]}
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

    def test_snapshot_canonical_hash_is_deterministic_and_sensitive_to_source_change(self) -> None:
        first = _snapshot(101, "AAPL", "hold", "0.71", outcome_id=301, alpha="0.012")
        reordered = dict(reversed(list(first.items())))
        payload = {"recommendation_snapshots": [first]}
        same_payload = {"recommendation_snapshots": [reordered]}

        first_snapshot = build_recommendation_eval_snapshots(payload)[0]
        same_snapshot = build_recommendation_eval_snapshots(same_payload)[0]
        self.assertEqual(first_snapshot.snapshot_sha256, same_snapshot.snapshot_sha256)
        self.assertEqual(len(first_snapshot.snapshot_sha256), 64)
        self.assertEqual(canonical_snapshot_json(first), canonical_snapshot_json(reordered))

        changed = json.loads(json.dumps(first))
        changed["recommendation"]["total_score"] = "0.72"
        changed_snapshot = build_recommendation_eval_snapshots({"recommendation_snapshots": [changed]})[0]
        self.assertNotEqual(first_snapshot.snapshot_sha256, changed_snapshot.snapshot_sha256)

    def test_snapshot_builder_rejects_missing_or_duplicate_source_identity(self) -> None:
        with self.assertRaises(ValueError):
            build_recommendation_eval_snapshots({})
        duplicate = _snapshot(101, "AAPL", "hold", "0.71", outcome_id=301, alpha="0.012")
        with self.assertRaises(ValueError):
            build_recommendation_eval_snapshots({"recommendation_snapshots": [duplicate, duplicate]})

    def test_render_eval_insert_sql_keeps_legacy_render_compatibility(self) -> None:
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
        self.assertNotIn("recommendation_eval_snapshot", sql)

    def test_render_executed_eval_persists_lineage_and_snapshots_atomically(self) -> None:
        snapshots = build_recommendation_eval_snapshots(_payload())
        sql = render_recommendation_quality_eval_insert_sql(
            eval_name=DEFAULT_EVAL_NAME,
            dataset_version="recommendation-quality-live-v1",
            provider="postgres",
            model_name="deterministic-sql-v1",
            score_json={"quality_status": "needs_more_data"},
            pipeline_run_id=9402,
            as_of_date=date(2026, 5, 24),
            horizon_days=30,
            config_json={"evaluation_only": True, "recommendation_scoring_mutated": False},
            snapshots=snapshots,
        )
        lowered = sql.lower()
        self.assertTrue(lowered.startswith("with inserted_eval as"))
        self.assertIn("pipeline_run_id", sql)
        self.assertIn("config_json", sql)
        self.assertIn("insert into ai.recommendation_eval_snapshot", sql)
        self.assertIn("snapshot_sha256", sql)
        self.assertIn("source_outcome_id", sql)
        self.assertIn("inserted_snapshots as", sql)
        self.assertNotIn("on conflict", lowered)
        self.assertNotIn("update ai.recommendation_eval_snapshot", lowered)
        self.assertNotIn("delete from ai.recommendation_eval_snapshot", lowered)

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
        self.assertEqual(report["snapshot_schema_version"], SNAPSHOT_SCHEMA_VERSION)
        self.assertEqual(report["snapshot_count"], 3)
        self.assertEqual(executor.non_query_sql, [])
        self.assertEqual(len(executor.scalar_sql), 1)

    def test_run_execute_records_pipeline_eval_lineage_and_snapshot_count(self) -> None:
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
        self.assertEqual(report["snapshot_count"], 3)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[2])
        self.assertIn("insert into ai.recommendation_eval_snapshot", executor.scalar_sql[2])
        self.assertIn("9402", executor.scalar_sql[2])
        self.assertIn("recommendation-eval-snapshot-v1", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


def _snapshot(
    recommendation_id: int,
    symbol: str,
    action: str,
    total_score: str,
    *,
    outcome_id: int | None,
    alpha: str | None,
) -> dict[str, object]:
    batch_id = 80 + recommendation_id
    thesis_id = 900 + recommendation_id
    selected_outcome = None
    if outcome_id is not None:
        selected_outcome = {
            "outcome_id": outcome_id,
            "recommendation_id": recommendation_id,
            "measurement_start_date": "2026-04-24",
            "measurement_end_date": "2026-05-24",
            "horizon_days": 30,
            "entry_price": "100.00",
            "exit_price": "103.00",
            "absolute_return_pct": "0.030000",
            "benchmark_code": "SPY",
            "benchmark_return_pct": "0.018000",
            "alpha_pct": alpha,
            "max_drawdown_pct": "-0.020000",
            "outcome_label": "positive",
            "source_run_id": 7001,
            "created_at": "2026-05-24T12:00:00+00:00",
        }
    return {
        "snapshot_schema_version": SNAPSHOT_SCHEMA_VERSION,
        "recommendation": {
            "recommendation_id": recommendation_id,
            "batch_id": batch_id,
            "instrument_id": 1000 + recommendation_id,
            "thesis_id": thesis_id,
            "bucket": "core",
            "action": action,
            "rank_position": 1,
            "total_score": total_score,
            "recommended_weight": "0.05",
            "status": "active",
        },
        "batch": {
            "batch_id": batch_id,
            "as_of_date": "2026-05-20",
            "market_code": "US",
            "strategy_name": "Long Term Paper",
            "horizon_type": "long_term",
            "universe_version": "us-v1",
            "notes": None,
            "source_run_id": 6001,
            "created_at": "2026-05-20T10:00:00+00:00",
        },
        "instrument": {"instrument_id": 1000 + recommendation_id, "primary_symbol": symbol},
        "thesis": {
            "thesis_id": thesis_id,
            "instrument_id": 1000 + recommendation_id,
            "primary_node_id": None,
            "thesis_type": "company",
            "title": f"{symbol} long-term thesis",
            "summary": "Durable thesis summary",
            "status": "active",
            "conviction_score": "0.72",
            "expected_holding_days": 365,
            "benchmark_code": "SPY",
            "entry_conditions": "valuation support",
            "invalidation_conditions": "fundamental deterioration",
            "exit_conditions": "thesis fulfilled",
            "created_at": "2026-05-19T10:00:00+00:00",
            "closed_at": None,
            "created_by_run_id": 5999,
        },
        "score_components": [
            {
                "component_name": "cycle_score",
                "component_score": "0.61",
                "component_weight": "0.00",
                "explanation": "cycle context",
                "created_at": "2026-05-20T10:00:00+00:00",
            }
        ],
        "selected_outcome": selected_outcome,
    }


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
        "recommendation_snapshots": [
            _snapshot(101, "AAPL", "hold", "0.71", outcome_id=301, alpha="0.012"),
            _snapshot(102, "MSFT", "watch", "0.68", outcome_id=302, alpha="-0.004"),
            _snapshot(103, "NVDA", "watch", "0.66", outcome_id=None, alpha=None),
        ],
    }


if __name__ == "__main__":
    unittest.main()
