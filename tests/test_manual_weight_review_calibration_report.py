from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.manual_weight_review_calibration_report import (
    DEFAULT_REPORT_NAME,
    build_manual_weight_review_calibration_report,
    render_manual_weight_review_audit_eval_lookup_sql,
    render_manual_weight_review_failure_case_lookup_sql,
    render_manual_weight_review_calibration_insert_sql,
    run_manual_weight_review_calibration_report,
)


class FakeManualWeightReviewExecutor:
    def __init__(self) -> None:
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []
        self.run_id = 9903
        self.eval_run_id = 603

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- manual weight review calibration source audit eval lookup"):
            return json.dumps(_audit_eval_payload())
        if sql.startswith("-- manual weight review calibration failure case lookup"):
            return json.dumps(_failure_cases())
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into ai.eval_run" in sql:
            return str(self.eval_run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class ManualWeightReviewCalibrationReportTests(unittest.TestCase):
    def test_render_audit_lookup_is_read_only(self) -> None:
        sql = render_manual_weight_review_audit_eval_lookup_sql(
            as_of_date=date(2026, 5, 25),
            audit_eval_run_id=16,
        )
        lowered = sql.lower()

        self.assertIn("-- manual weight review calibration source audit eval lookup", sql)
        self.assertIn("eval_run.eval_run_id = 16", sql)
        self.assertNotIn("created_at::date <=", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_render_latest_audit_lookup_uses_as_of_date_when_id_is_not_explicit(self) -> None:
        sql = render_manual_weight_review_audit_eval_lookup_sql(as_of_date=date(2026, 5, 25))

        self.assertIn("created_at::date <= '2026-05-25'::date", sql)
        self.assertNotIn("eval_run.eval_run_id =", sql)

    def test_render_failure_case_lookup_is_read_only_and_bounded(self) -> None:
        sql = render_manual_weight_review_failure_case_lookup_sql(
            as_of_date=date(2026, 5, 25),
            horizon_days=30,
            limit=7,
        )
        lowered = sql.lower()

        self.assertIn("-- manual weight review calibration failure case lookup", sql)
        self.assertIn("performance.recommendation_outcome", sql)
        self.assertIn("outcome.measurement_start_date >= recommendation.recommendation_date", sql)
        self.assertIn("outcome.measurement_end_date >= outcome.measurement_start_date", sql)
        self.assertIn("limit 7", lowered)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_build_report_keeps_automatic_weight_and_broker_disabled(self) -> None:
        report = build_manual_weight_review_calibration_report(
            as_of_date=date(2026, 5, 25),
            audit_eval=_audit_eval_payload(),
            failure_cases=_failure_cases(),
        )

        self.assertEqual(report["report_name"], DEFAULT_REPORT_NAME)
        self.assertEqual(report["decision"], "manual_review_allowed_keep_weights_collect_more_evidence")
        self.assertTrue(report["manual_weight_review_allowed"])
        self.assertFalse(report["automatic_weight_change_allowed"])
        self.assertFalse(report["automatic_order_allowed"])
        self.assertFalse(report["broker_submit_allowed"])
        self.assertFalse(report["recommendation_scoring_mutated"])
        self.assertEqual(report["component_summary"]["keep_zero_or_do_not_increase_count"], 2)
        self.assertEqual(report["component_summary"]["already_weighted_review_only_count"], 1)
        self.assertEqual(report["failure_case_examples"][0]["symbol"], "QUBT")
        self.assertEqual(report["source_audit_eval"]["outcome_calibration_eval_run_id"], 27)
        self.assertEqual(report["source_audit_eval"]["outcome_calibration_status"], "ready_for_manual_weight_review")
        self.assertEqual(report["outcome_calibration_gate"]["status"], "ready_for_manual_weight_review")
        self.assertIn("현재 추천 weight를 유지한다.", report["next_actions"])

    def test_render_insert_records_eval_run_without_mutating_weights(self) -> None:
        sql = render_manual_weight_review_calibration_insert_sql(
            score_json={"decision": "manual_review_allowed_keep_weights_collect_more_evidence"}
        )
        lowered = sql.lower()

        self.assertIn("insert into ai.eval_run", lowered)
        self.assertIn("manual_weight_review_calibration_report", sql)
        self.assertNotIn("signal.recommendation_score_component", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_run_execute_records_pipeline_and_report_eval_without_weight_mutation(self) -> None:
        executor = FakeManualWeightReviewExecutor()

        report = run_manual_weight_review_calibration_report(
            config=RuntimeConfig(psql_command="docker exec psql"),
            as_of_date=date(2026, 5, 25),
            audit_eval_run_id=16,
            failure_case_limit=5,
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9903)
        self.assertEqual(report["report_eval_run_id"], 603)
        self.assertFalse(report["automatic_weight_change_allowed"])
        self.assertIn("-- manual weight review calibration source audit eval lookup", executor.scalar_sql[0])
        self.assertIn("-- manual weight review calibration failure case lookup", executor.scalar_sql[1])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[2])
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[3])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


def _audit_eval_payload() -> dict[str, object]:
    return {
        "eval_run_id": 16,
        "eval_name": "recommendation_weight_review_readiness_audit",
        "dataset_version": "recommendation-weight-review-readiness-v1",
        "provider": "postgres",
        "model_name": "deterministic-guardrail-v1",
        "created_at": "2026-05-25T15:00:00Z",
        "score_json": {
            "source_eval_run_id": 13,
            "source_quality_status": "ready_for_weight_review",
            "decision": "ready_for_manual_weight_review",
            "manual_weight_review_allowed": True,
            "automatic_weight_change_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "recommendation_scoring_mutated": False,
            "sample": {
                "sample_status": "sufficient_sample",
                "outcome_count": 30,
                "positive_outcome_count": 3,
                "positive_outcome_rate": 0.1,
                "horizon_days": 30,
            },
            "outcome_calibration_gate": {
                "status": "ready_for_manual_weight_review",
                "eval_run_id": 27,
                "horizon_days": [30, 90, 180, 365],
                "outcome_count": 30,
                "recommendation_horizon_count": 180,
                "ready_for_backfill_count": 0,
                "next_action": "표본과 coverage 기준은 충족했다.",
            },
            "component_reviews": [
                {
                    "component_name": "momentum_score",
                    "outcome_count": 30,
                    "positive_score_spread": "0.38",
                    "avg_component_weight": "0.25",
                    "readiness": "already_weighted_review_only",
                    "automatic_weight_change_allowed": False,
                },
                {
                    "component_name": "valuation_margin_score",
                    "outcome_count": 5,
                    "positive_score_spread": "-0.48",
                    "avg_component_weight": "0",
                    "readiness": "do_not_increase_weight",
                    "automatic_weight_change_allowed": False,
                },
                {
                    "component_name": "fundamental_quality_score",
                    "outcome_count": 5,
                    "positive_score_spread": "-0.53",
                    "avg_component_weight": "0",
                    "readiness": "do_not_increase_weight",
                    "automatic_weight_change_allowed": False,
                },
            ],
        },
    }


def _failure_cases() -> list[dict[str, object]]:
    return [
        {
            "recommendation_id": 251,
            "primary_symbol": "QUBT",
            "bucket": "watch",
            "action": "monitor",
            "total_score": "0.42",
            "recommendation_date": "2026-05-01",
            "outcome_label": "underperform",
            "alpha_pct": "-0.12",
            "max_drawdown_pct": "-0.25",
            "measurement_end_date": "2026-05-25",
            "component_scores": [
                {"component_name": "valuation_margin_score", "component_score": "0.2", "component_weight": "0"},
                {"component_name": "momentum_score", "component_score": "0.8", "component_weight": "0.25"},
            ],
        }
    ]


if __name__ == "__main__":
    unittest.main()
