from __future__ import annotations

import json
import unittest
from datetime import date
from unittest.mock import patch

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.recommendation_outcome_calibration_sample_expansion import (
    DEFAULT_EVAL_NAME,
    build_recommendation_outcome_calibration_score,
    render_recommendation_outcome_calibration_eval_insert_sql,
    render_recommendation_outcome_sample_audit_sql,
    run_recommendation_outcome_calibration_sample_expansion,
)


class FakeOutcomeCalibrationExecutor:
    def __init__(self, *, run_id: int = 9901, eval_run_id: int = 7701) -> None:
        self.run_id = run_id
        self.eval_run_id = eval_run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- recommendation outcome calibration sample audit lookup"):
            return json.dumps(_sample_audit_payload())
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into ai.eval_run" in sql:
            return str(self.eval_run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql[:160]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class RecommendationOutcomeCalibrationSampleExpansionTests(unittest.TestCase):
    def test_render_sample_audit_sql_is_read_only_and_reports_missing_reasons(self) -> None:
        sql = render_recommendation_outcome_sample_audit_sql(
            as_of_date=date(2026, 5, 27),
            horizon_days=(30, 90),
            market_code="US",
            strategy_name="long_term_core",
            horizon_type="long_term",
            universe_version="live-v1",
        )
        lowered = sql.lower()

        self.assertIn("-- recommendation outcome calibration sample audit lookup", sql)
        self.assertIn("horizon_days(horizon_day)", sql)
        self.assertIn("ready_for_backfill", sql)
        self.assertIn("missing_entry_price", sql)
        self.assertIn("missing_exit_price", sql)
        self.assertIn("component_calibration_diagnostics", sql)
        self.assertIn("performance.recommendation_outcome", sql)
        self.assertIn("signal.recommendation_score_component", sql)
        self.assertIn("'fundamental_quality_score'", sql)
        self.assertIn("'cycle_conflict_penalty'", sql)
        self.assertIn("batch.strategy_name = 'long_term_core'", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_build_score_blocks_weight_changes_when_backfill_candidates_remain(self) -> None:
        score = build_recommendation_outcome_calibration_score(
            as_of_date=date(2026, 5, 27),
            horizon_days=(30, 90),
            sample_audit_before=_sample_audit_payload(outcome_count=1, ready_count=2),
            sample_audit_after=_sample_audit_payload(outcome_count=2, ready_count=1),
            backfill_report={"status": "executed", "recommendation_outcome_count": 1},
            quality_report={"score": {"quality_status": "needs_more_data", "sample_status": "insufficient_sample"}},
        )

        self.assertEqual(score["status"], "backfill_candidates_remain")
        self.assertFalse(score["recommendation_scoring_mutated"])
        self.assertFalse(score["automatic_order_allowed"])
        self.assertFalse(score["broker_submit_allowed"])
        self.assertEqual(score["order_boundary"], "read_only_no_order")
        self.assertEqual(score["outcome_delta"]["outcome_count_added_or_found"], 1)
        self.assertIn("성과 검증 후보", score["next_action"])

    def test_render_eval_insert_sql_uses_dedicated_eval_name(self) -> None:
        sql = render_recommendation_outcome_calibration_eval_insert_sql(
            score_json={"status": "collect_more_outcomes_keep_weights"}
        )

        self.assertIn("insert into ai.eval_run", sql)
        self.assertIn(DEFAULT_EVAL_NAME, sql)
        self.assertIn("recommendation-outcome-calibration-sample-expansion-v1", sql)

    def test_run_dry_run_collects_audit_backfill_preview_and_quality_preview_without_writes(self) -> None:
        executor = FakeOutcomeCalibrationExecutor()
        with (
            patch(
                "stockanalysis.operations.recommendation_outcome_calibration_sample_expansion.run_recommendation_outcome_backfill"
            ) as backfill_mock,
            patch(
                "stockanalysis.operations.recommendation_outcome_calibration_sample_expansion.run_recommendation_quality_eval"
            ) as quality_mock,
        ):
            backfill_mock.return_value = {
                "status": "preview_candidates_available",
                "mode": "preview",
                "candidate_count": 1,
                "missing_outcome_count": 1,
            }
            quality_mock.return_value = {
                "status": "planned",
                "score": {"quality_status": "needs_more_data", "sample_status": "insufficient_sample"},
            }
            report = run_recommendation_outcome_calibration_sample_expansion(
                config=RuntimeConfig(psql_command="psql"),
                as_of_date=date(2026, 5, 27),
                horizon_days=(30,),
                execute=False,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["score"]["status"], "backfill_candidates_remain")
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertEqual(executor.non_query_sql, [])
        self.assertFalse(backfill_mock.call_args.kwargs["execute"])
        self.assertFalse(quality_mock.call_args.kwargs["execute"])

    def test_run_execute_records_pipeline_eval_and_keeps_order_boundary_read_only(self) -> None:
        executor = FakeOutcomeCalibrationExecutor(run_id=9902, eval_run_id=7702)
        with (
            patch(
                "stockanalysis.operations.recommendation_outcome_calibration_sample_expansion.run_recommendation_outcome_backfill"
            ) as backfill_mock,
            patch(
                "stockanalysis.operations.recommendation_outcome_calibration_sample_expansion.run_recommendation_quality_eval"
            ) as quality_mock,
        ):
            backfill_mock.return_value = {
                "status": "executed",
                "mode": "execute",
                "candidate_count": 1,
                "missing_outcome_count": 1,
                "recommendation_outcome_count": 1,
                "thesis_outcome_count": 1,
            }
            quality_mock.return_value = {
                "status": "completed",
                "eval_run_id": 7001,
                "score": {"quality_status": "needs_more_data", "sample_status": "insufficient_sample"},
            }
            report = run_recommendation_outcome_calibration_sample_expansion(
                config=RuntimeConfig(psql_command="psql"),
                as_of_date=date(2026, 5, 27),
                horizon_days=(30,),
                execute=True,
                executor=executor,  # type: ignore[arg-type]
            )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9902)
        self.assertEqual(report["eval_run_id"], 7702)
        self.assertEqual(report["score"]["order_boundary"], "read_only_no_order")
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[-1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])
        self.assertTrue(backfill_mock.call_args.kwargs["execute"])
        self.assertTrue(quality_mock.call_args.kwargs["execute"])


def _sample_audit_payload(*, outcome_count: int = 2, ready_count: int = 1) -> dict[str, object]:
    return {
        "as_of_date": "2026-05-27",
        "horizon_days": [30],
        "filters": {},
        "summary": {
            "recommendation_horizon_count": 4,
            "recommendation_count": 4,
            "outcome_count": outcome_count,
            "ready_for_backfill_count": ready_count,
            "not_due_count": 0,
            "missing_entry_price_count": 0,
            "missing_exit_price_count": 0,
            "benchmark_warning_count": 0,
            "outcome_coverage_rate": "0.50000000",
        },
        "horizon_coverage": [
            {
                "horizon_day": 30,
                "recommendation_horizon_count": 4,
                "outcome_count": outcome_count,
                "ready_for_backfill_count": ready_count,
                "not_due_count": 0,
                "price_gap_count": 0,
            }
        ],
        "missing_reason_counts": {"outcome_recorded": outcome_count, "ready_for_backfill": ready_count},
        "missing_examples": [],
        "component_calibration_diagnostics": [
            {
                "component_name": "fundamental_quality_score",
                "component_row_count": 4,
                "outcome_count": outcome_count,
                "zero_weight_row_count": 4,
                "positive_score_spread": "0.12000000",
            }
        ],
        "guardrails": {
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
        },
    }


if __name__ == "__main__":
    unittest.main()
