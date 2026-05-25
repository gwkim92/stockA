from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.recommendation_weight_review_readiness_audit import (
    DEFAULT_AUDIT_EVAL_NAME,
    READY_DECISION,
    audit_recommendation_weight_review_readiness,
    render_recommendation_weight_review_audit_insert_sql,
    render_recommendation_weight_review_eval_lookup_sql,
    run_recommendation_weight_review_readiness_audit,
)


class FakeWeightReviewAuditExecutor:
    def __init__(self, *, run_id: int = 9901, audit_eval_run_id: int = 601) -> None:
        self.run_id = run_id
        self.audit_eval_run_id = audit_eval_run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- recommendation weight review readiness audit source eval lookup"):
            return json.dumps(
                {
                    "eval_run_id": 11,
                    "eval_name": "recommendation_quality_calibration",
                    "dataset_version": "recommendation-quality-live-v1",
                    "provider": "postgres",
                    "model_name": "deterministic-sql-v1",
                    "score_json": _ready_score_with_paper_conflict(),
                    "created_at": "2026-05-25T12:00:00Z",
                }
            )
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        if "insert into ai.eval_run" in sql:
            return str(self.audit_eval_run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql[:120]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class RecommendationWeightReviewReadinessAuditTests(unittest.TestCase):
    def test_render_lookup_sql_reads_latest_quality_eval_without_writes(self) -> None:
        sql = render_recommendation_weight_review_eval_lookup_sql(
            as_of_date=date(2026, 5, 25),
            eval_run_id=11,
        )
        lowered = sql.lower()

        self.assertIn("-- recommendation weight review readiness audit source eval lookup", sql)
        self.assertIn("eval_run.eval_run_id = 11", sql)
        self.assertIn("'2026-05-25'::date", sql)
        self.assertIn("'recommendation_quality_calibration'", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_audit_blocks_ready_quality_eval_when_paper_validation_has_conflicts(self) -> None:
        audit = audit_recommendation_weight_review_readiness(
            _ready_score_with_paper_conflict(),
            source_eval_run_id=11,
        )

        self.assertEqual(audit["decision"], "blocked_by_paper_validation_conflicts")
        self.assertFalse(audit["manual_weight_review_allowed"])
        self.assertFalse(audit["automatic_weight_change_allowed"])
        self.assertFalse(audit["recommendation_scoring_mutated"])
        self.assertEqual(audit["paper_validation"]["conflict_count"], 3)
        self.assertIn("paper validation conflict", audit["next_action"])

    def test_audit_allows_manual_review_only_when_all_guardrails_pass(self) -> None:
        score = _ready_score_with_paper_conflict()
        score["paper_validation"] = {
            "latest_status": "passed",
            "validation_date": "2026-05-25",
            "recommendation_count": 6,
            "conflict_count": 0,
            "approved_action_count": 2,
        }

        audit = audit_recommendation_weight_review_readiness(score, source_eval_run_id=11)

        self.assertEqual(audit["decision"], READY_DECISION)
        self.assertTrue(audit["manual_weight_review_allowed"])
        self.assertFalse(audit["automatic_weight_change_allowed"])
        self.assertEqual(audit["blockers"], [])
        self.assertEqual(audit["component_reviews"][0]["readiness"], "eligible_for_manual_pilot_review")

    def test_audit_distinguishes_failed_validation_without_conflicts(self) -> None:
        score = _ready_score_with_paper_conflict()
        score["paper_validation"] = {
            "latest_status": "failed",
            "validation_date": "2026-05-25",
            "recommendation_count": 6,
            "conflict_count": 0,
            "approved_action_count": 0,
        }

        audit = audit_recommendation_weight_review_readiness(score, source_eval_run_id=13)

        self.assertEqual(audit["decision"], "blocked_by_paper_validation_failed")
        self.assertEqual(audit["blockers"][0]["code"], "blocked_by_paper_validation_failed")
        self.assertIn("safety interlock", audit["next_action"])

    def test_render_audit_insert_sql_records_audit_as_ai_eval_run(self) -> None:
        sql = render_recommendation_weight_review_audit_insert_sql(
            score_json={"decision": "blocked_by_paper_validation_conflicts"}
        )

        self.assertIn("insert into ai.eval_run", sql)
        self.assertIn(DEFAULT_AUDIT_EVAL_NAME, sql)
        self.assertIn("recommendation-weight-review-readiness-v1", sql)

    def test_run_dry_run_reads_source_eval_without_writes(self) -> None:
        executor = FakeWeightReviewAuditExecutor()

        report = run_recommendation_weight_review_readiness_audit(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            eval_run_id=11,
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["audit"]["decision"], "blocked_by_paper_validation_conflicts")
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertEqual(executor.non_query_sql, [])

    def test_run_execute_records_pipeline_and_audit_eval_run_without_weight_mutation(self) -> None:
        executor = FakeWeightReviewAuditExecutor(run_id=9902, audit_eval_run_id=602)

        report = run_recommendation_weight_review_readiness_audit(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            eval_run_id=11,
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9902)
        self.assertEqual(report["audit_eval_run_id"], 602)
        self.assertFalse(report["audit"]["automatic_weight_change_allowed"])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[2])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])


def _ready_score_with_paper_conflict() -> dict[str, object]:
    return {
        "eval_name": "recommendation_quality_calibration",
        "dataset_version": "recommendation-quality-live-v1",
        "as_of_date": "2026-05-25",
        "horizon_days": 30,
        "quality_status": "ready_for_weight_review",
        "sample_status": "sufficient_sample",
        "recommendation_count": 36,
        "outcome_count": 30,
        "outcome_coverage_rate": 0.833333,
        "positive_outcome_count": 3,
        "positive_outcome_rate": 0.1,
        "cycle_weight_guardrail": {
            "cycle_weight_unchanged": True,
            "recommendation_scoring_mutated": False,
        },
        "fundamental_weight_guardrail": {
            "fundamental_weight_unchanged": True,
            "recommendation_scoring_mutated": False,
        },
        "professional_analysis_coverage": {
            "status": "sufficient_coverage",
            "recommendation_count": 36,
            "complete_professional_coverage_count": 30,
            "complete_professional_coverage_rate": 0.833333,
        },
        "paper_validation": {
            "latest_status": "failed",
            "validation_date": "2026-05-25",
            "recommendation_count": 6,
            "conflict_count": 3,
            "approved_action_count": 0,
        },
        "component_metrics": [
            {
                "component_name": "momentum_score",
                "outcome_count": 30,
                "positive_score_spread": "0.38093333",
                "avg_component_weight": "0.00000000",
            },
            {
                "component_name": "valuation_margin_score",
                "outcome_count": 5,
                "positive_score_spread": "-0.12000000",
                "avg_component_weight": "0.00000000",
            },
        ],
    }


if __name__ == "__main__":
    unittest.main()
