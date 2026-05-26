from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.operations.portfolio_review_feedback_cadence import (
    DEFAULT_DATASET_VERSION,
    DEFAULT_EVAL_NAME,
    build_portfolio_review_feedback_cadence,
    render_portfolio_review_feedback_cadence_context_sql,
    render_portfolio_review_feedback_cadence_insert_sql,
    run_portfolio_review_feedback_cadence,
)


class FakeCadenceExecutor:
    def __init__(self, context: dict[str, object]) -> None:
        self.context = context
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if sql.startswith("-- portfolio review feedback cadence context lookup"):
            return json.dumps(self.context)
        if "insert into ops.pipeline_run" in lowered:
            return "9401"
        if "insert into ai.eval_run" in lowered:
            return "8401"
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PortfolioReviewFeedbackCadenceTests(unittest.TestCase):
    def test_young_history_waits_for_outcome_window(self) -> None:
        cadence = build_portfolio_review_feedback_cadence(
            context=_context(history_age_days=2, feedback_status="missing", calibration_status="missing"),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )

        self.assertEqual(cadence["eval_name"], DEFAULT_EVAL_NAME)
        self.assertEqual(cadence["dataset_version"], DEFAULT_DATASET_VERSION)
        self.assertEqual(cadence["cadence_status"], "wait_for_outcome_window")
        self.assertFalse(cadence["should_run_now"])
        self.assertTrue(cadence["should_wait"])
        self.assertFalse(cadence["automatic_order_allowed"])
        self.assertFalse(cadence["broker_submit_allowed"])

    def test_mature_history_without_latest_feedback_requests_feedback_now(self) -> None:
        cadence = build_portfolio_review_feedback_cadence(
            context=_context(history_age_days=45, feedback_status="missing", calibration_status="missing"),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )

        self.assertEqual(cadence["cadence_status"], "run_feedback_now")
        self.assertTrue(cadence["should_run_now"])
        self.assertIn("portfolio-review-decision-outcome-feedback-run", cadence["command"])
        self.assertIn("--history-eval-run-id 31", cadence["command"])
        self.assertIn("portfolio-review-feedback-calibration-run", cadence["follow_up_command"])

    def test_latest_feedback_without_calibration_requests_calibration_now(self) -> None:
        cadence = build_portfolio_review_feedback_cadence(
            context=_context(history_age_days=45, feedback_status="loaded", calibration_status="missing"),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )

        self.assertEqual(cadence["cadence_status"], "run_calibration_now")
        self.assertTrue(cadence["should_run_now"])
        self.assertIn("portfolio-review-feedback-calibration-run", cadence["command"])

    def test_latest_feedback_and_calibration_are_current(self) -> None:
        cadence = build_portfolio_review_feedback_cadence(
            context=_context(
                history_age_days=45,
                feedback_status="loaded",
                calibration_status="loaded",
                calibration_feedback_run_ids=[32],
            ),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )

        self.assertEqual(cadence["cadence_status"], "calibration_current")
        self.assertFalse(cadence["should_run_now"])
        self.assertTrue(cadence["should_wait"])
        self.assertEqual(cadence["order_boundary"], "read_only_no_order")

    def test_missing_history_blocks_review(self) -> None:
        cadence = build_portfolio_review_feedback_cadence(
            context={
                "history": {"status": "missing", "decision_count": 0},
                "feedback": {"status": "missing"},
                "calibration": {"status": "missing"},
                "evidence": {"decision_count": 0},
            },
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )

        self.assertEqual(cadence["cadence_status"], "missing_evidence_review_required")
        self.assertFalse(cadence["should_run_now"])
        self.assertIn("portfolio-review-decision-history-run", cadence["command"])

    def test_sql_renderers_are_read_only_except_eval_insert(self) -> None:
        lookup_sql = render_portfolio_review_feedback_cadence_context_sql(
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )
        insert_sql = render_portfolio_review_feedback_cadence_insert_sql(
            score_json={"cadence_status": "run_feedback_now"}
        )
        lowered_lookup = lookup_sql.lower()
        lowered_insert = insert_sql.lower()

        self.assertIn("portfolio_review_decision_history", lookup_sql)
        self.assertIn("portfolio_review_decision_outcome_feedback", lookup_sql)
        self.assertIn("portfolio_review_feedback_calibration", lookup_sql)
        self.assertIn("performance.recommendation_outcome", lowered_lookup)
        self.assertIn("trading.paper_validation_run", lowered_lookup)
        self.assertIn("market.daily_price_bar", lowered_lookup)
        self.assertNotIn("insert into", lowered_lookup)
        self.assertNotIn("update ", lowered_lookup)
        self.assertNotIn("delete from", lowered_lookup)
        self.assertIn("insert into ai.eval_run", lowered_insert)
        self.assertIn(DEFAULT_EVAL_NAME, insert_sql)
        self.assertIn(DEFAULT_DATASET_VERSION, insert_sql)
        self.assertNotIn("signal.recommendation_score_component", lowered_insert)
        self.assertNotIn("portfolio.position_snapshot", lowered_insert)
        self.assertNotIn("join broker", lowered_insert)

    def test_run_execute_records_pipeline_and_eval_run(self) -> None:
        executor = FakeCadenceExecutor(_context(history_age_days=45, feedback_status="missing"))

        report = run_portfolio_review_feedback_cadence(
            config=type("Config", (), {"psql_command": "psql"})(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9401)
        self.assertEqual(report["eval_run_id"], 8401)
        self.assertIn("portfolio review feedback cadence context lookup", executor.scalar_sql[0])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1].lower())
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[2].lower())
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])


def _context(
    *,
    history_age_days: int,
    feedback_status: str,
    calibration_status: str = "missing",
    calibration_feedback_run_ids: list[int] | None = None,
) -> dict[str, object]:
    calibration_feedback_run_ids = calibration_feedback_run_ids or []
    return {
        "history": {
            "status": "loaded",
            "eval_run_id": 31,
            "created_at": "2026-05-25T01:00:00+00:00",
            "as_of_date": "2026-04-12" if history_age_days >= 30 else "2026-05-25",
            "decision_status": "review_required",
            "decision_count": 2,
            "review_required_count": 2,
        },
        "feedback": {
            "status": feedback_status,
            "eval_run_id": 32 if feedback_status == "loaded" else None,
            "created_at": "2026-05-27T01:00:00+00:00" if feedback_status == "loaded" else "",
            "as_of_date": "2026-05-27" if feedback_status == "loaded" else "",
            "source_history_eval_run_id": 31 if feedback_status == "loaded" else None,
            "source_history_as_of_date": "2026-04-12",
            "feedback_status": "validated" if feedback_status == "loaded" else "missing",
            "decision_count": 2 if feedback_status == "loaded" else 0,
            "validated_count": 2 if feedback_status == "loaded" else 0,
        },
        "calibration": {
            "status": calibration_status,
            "eval_run_id": 33 if calibration_status == "loaded" else None,
            "created_at": "2026-05-27T02:00:00+00:00" if calibration_status == "loaded" else "",
            "as_of_date": "2026-05-27" if calibration_status == "loaded" else "",
            "calibration_status": "manual_review_ready" if calibration_status == "loaded" else "missing",
            "feedback_run_count": 1 if calibration_status == "loaded" else 0,
            "decision_count": 2 if calibration_status == "loaded" else 0,
            "mature_decision_count": 2 if calibration_status == "loaded" else 0,
            "latest_feedback_runs": [{"eval_run_id": run_id} for run_id in calibration_feedback_run_ids],
        },
        "evidence": {
            "history_age_days": history_age_days,
            "decision_count": 2,
            "recommendation_link_count": 2,
            "recommendation_outcome_count": 1,
            "price_evidence_count": 2,
            "paper_validation": {
                "paper_validation_run_id": 12,
                "validation_date": "2026-05-27",
                "status": "completed",
                "recommendation_count": 2,
                "conflict_count": 0,
                "approved_action_count": 0,
            },
        },
    }


if __name__ == "__main__":
    unittest.main()
