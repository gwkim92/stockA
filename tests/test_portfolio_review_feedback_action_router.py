from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.operations.portfolio_review_feedback_action_router import (
    DEFAULT_DATASET_VERSION,
    DEFAULT_EVAL_NAME,
    build_portfolio_review_feedback_action_router_decision,
    render_portfolio_review_feedback_action_router_context_sql,
    render_portfolio_review_feedback_action_router_insert_sql,
    run_portfolio_review_feedback_action_router,
)


class FakeActionRouterExecutor:
    def __init__(self, context: dict[str, object]) -> None:
        self.context = context
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if sql.startswith("-- portfolio review feedback action router context lookup"):
            return json.dumps(self.context)
        if "insert into ops.pipeline_run" in lowered:
            return "9501"
        if "insert into ai.eval_run" in lowered:
            return "8501"
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PortfolioReviewFeedbackActionRouterTests(unittest.TestCase):
    def test_missing_cadence_records_no_op(self) -> None:
        action = build_portfolio_review_feedback_action_router_decision(
            context={"status": "missing", "score_json": {}},
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )

        self.assertEqual(action["route_action"], "no_op")
        self.assertEqual(action["action_status"], "no_op_missing_cadence")
        self.assertFalse(action["automatic_order_allowed"])
        self.assertFalse(action["broker_submit_allowed"])

    def test_wait_for_outcome_window_records_no_op(self) -> None:
        action = build_portfolio_review_feedback_action_router_decision(
            context=_context(cadence_status="wait_for_outcome_window", action_type="wait", should_run_now=False),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )

        self.assertEqual(action["route_action"], "no_op")
        self.assertEqual(action["action_status"], "no_op_wait_for_outcome_window")
        self.assertEqual(action["source_cadence_eval_run_id"], 34)

    def test_run_feedback_status_routes_to_feedback_runner(self) -> None:
        action = build_portfolio_review_feedback_action_router_decision(
            context=_context(cadence_status="run_feedback_now", action_type="execute_feedback", should_run_now=True),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 6, 30),
        )

        self.assertEqual(action["route_action"], "execute_feedback")
        self.assertEqual(action["action_status"], "execute_feedback_ready")
        self.assertEqual(action["history_eval_run_id"], 31)
        self.assertIn("portfolio-review-decision-outcome-feedback-run", action["next_action"])

    def test_run_calibration_status_routes_to_calibration_runner(self) -> None:
        action = build_portfolio_review_feedback_action_router_decision(
            context=_context(
                cadence_status="run_calibration_now",
                action_type="execute_calibration",
                should_run_now=True,
            ),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 6, 30),
        )

        self.assertEqual(action["route_action"], "execute_calibration")
        self.assertEqual(action["action_status"], "execute_calibration_ready")
        self.assertIn("portfolio-review-feedback-calibration-run", action["next_action"])

    def test_guardrail_violation_blocks_supported_runner(self) -> None:
        context = _context(cadence_status="run_feedback_now", action_type="execute_feedback", should_run_now=True)
        context["score_json"]["broker_submit_allowed"] = True  # type: ignore[index]

        action = build_portfolio_review_feedback_action_router_decision(
            context=context,
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 6, 30),
        )

        self.assertEqual(action["route_action"], "no_op")
        self.assertEqual(action["action_status"], "blocked_guardrail_violation")

    def test_sql_renderers_are_read_only_except_action_audit_insert(self) -> None:
        lookup_sql = render_portfolio_review_feedback_action_router_context_sql(
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )
        insert_sql = render_portfolio_review_feedback_action_router_insert_sql(
            score_json={"action_status": "no_op_wait_for_outcome_window"}
        )
        lowered_lookup = lookup_sql.lower()
        lowered_insert = insert_sql.lower()

        self.assertIn("from ai.eval_run", lookup_sql)
        self.assertIn("portfolio_review_feedback_cadence", lookup_sql)
        self.assertIn("portfolio-review-feedback-cadence-v1", lookup_sql)
        self.assertNotIn("insert into", lowered_lookup)
        self.assertNotIn("update ", lowered_lookup)
        self.assertNotIn("delete from", lowered_lookup)
        self.assertIn("insert into ai.eval_run", lowered_insert)
        self.assertIn(DEFAULT_EVAL_NAME, insert_sql)
        self.assertIn(DEFAULT_DATASET_VERSION, insert_sql)
        self.assertNotIn("signal.recommendation_score_component", lowered_insert)
        self.assertNotIn("portfolio.position_snapshot", lowered_insert)
        self.assertNotIn("join broker", lowered_insert)

    def test_run_execute_feedback_invokes_only_feedback_runner_and_records_audit(self) -> None:
        executor = FakeActionRouterExecutor(
            _context(cadence_status="run_feedback_now", action_type="execute_feedback", should_run_now=True)
        )
        calls: dict[str, list[dict[str, object]]] = {"feedback": [], "calibration": []}

        def feedback_runner(**kwargs: object) -> dict[str, object]:
            calls["feedback"].append(kwargs)
            return {
                "report_name": "portfolio_review_decision_outcome_feedback",
                "status": "completed",
                "run_id": 9601,
                "eval_run_id": 8601,
                "feedback": {"feedback_status": "validated"},
            }

        def calibration_runner(**kwargs: object) -> dict[str, object]:
            calls["calibration"].append(kwargs)
            raise AssertionError("calibration runner should not execute")

        report = run_portfolio_review_feedback_action_router(
            config=type("Config", (), {"psql_command": "psql"})(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 6, 30),
            execute=True,
            executor=executor,
            feedback_runner=feedback_runner,
            calibration_runner=calibration_runner,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9501)
        self.assertEqual(report["eval_run_id"], 8501)
        self.assertEqual(report["action"]["action_status"], "feedback_executed")  # type: ignore[index]
        self.assertEqual(report["action"]["child_runner"]["eval_run_id"], 8601)  # type: ignore[index]
        self.assertEqual(len(calls["feedback"]), 1)
        self.assertEqual(calls["feedback"][0]["history_eval_run_id"], 31)
        self.assertEqual(calls["feedback"][0]["execute"], True)
        self.assertEqual(calls["calibration"], [])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1].lower())
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[2].lower())
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_execute_calibration_invokes_only_calibration_runner_and_records_audit(self) -> None:
        executor = FakeActionRouterExecutor(
            _context(cadence_status="run_calibration_now", action_type="execute_calibration", should_run_now=True)
        )
        calls: dict[str, list[dict[str, object]]] = {"feedback": [], "calibration": []}

        def feedback_runner(**kwargs: object) -> dict[str, object]:
            calls["feedback"].append(kwargs)
            raise AssertionError("feedback runner should not execute")

        def calibration_runner(**kwargs: object) -> dict[str, object]:
            calls["calibration"].append(kwargs)
            return {
                "report_name": "portfolio_review_feedback_calibration",
                "status": "completed",
                "run_id": 9602,
                "eval_run_id": 8602,
                "calibration": {"calibration_status": "collect_more_feedback"},
            }

        report = run_portfolio_review_feedback_action_router(
            config=type("Config", (), {"psql_command": "psql"})(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 6, 30),
            execute=True,
            executor=executor,
            feedback_runner=feedback_runner,
            calibration_runner=calibration_runner,
        )

        self.assertEqual(report["action"]["action_status"], "calibration_executed")  # type: ignore[index]
        self.assertEqual(report["action"]["child_runner"]["eval_run_id"], 8602)  # type: ignore[index]
        self.assertEqual(calls["feedback"], [])
        self.assertEqual(len(calls["calibration"]), 1)
        self.assertEqual(calls["calibration"][0]["execute"], True)

    def test_run_execute_no_op_records_audit_without_child_runner(self) -> None:
        executor = FakeActionRouterExecutor(
            _context(cadence_status="wait_for_outcome_window", action_type="wait", should_run_now=False)
        )
        calls: dict[str, list[dict[str, object]]] = {"feedback": [], "calibration": []}

        report = run_portfolio_review_feedback_action_router(
            config=type("Config", (), {"psql_command": "psql"})(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            execute=True,
            executor=executor,
            feedback_runner=lambda **kwargs: calls["feedback"].append(kwargs) or {},
            calibration_runner=lambda **kwargs: calls["calibration"].append(kwargs) or {},
        )

        self.assertEqual(report["action"]["action_status"], "no_op_wait_for_outcome_window")  # type: ignore[index]
        self.assertFalse(report["action"]["child_runner"]["executed"])  # type: ignore[index]
        self.assertEqual(calls["feedback"], [])
        self.assertEqual(calls["calibration"], [])
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[2].lower())


def _context(*, cadence_status: str, action_type: str, should_run_now: bool) -> dict[str, object]:
    return {
        "status": "loaded",
        "eval_run_id": 34,
        "created_at": "2026-05-27T08:00:00+00:00",
        "eval_name": "portfolio_review_feedback_cadence",
        "dataset_version": "portfolio-review-feedback-cadence-v1",
        "score_json": {
            "as_of_date": "2026-05-27",
            "portfolio_name": "Long Term Paper",
            "cadence_status": cadence_status,
            "action_type": action_type,
            "should_run_now": should_run_now,
            "should_wait": not should_run_now,
            "history": {
                "status": "loaded",
                "eval_run_id": 31,
                "as_of_date": "2026-05-25",
                "decision_count": 11,
            },
            "feedback": {
                "status": "loaded",
                "eval_run_id": 32,
                "feedback_status": "too_early",
                "source_history_eval_run_id": 31,
            },
            "calibration": {
                "status": "loaded",
                "eval_run_id": 33,
                "calibration_status": "insufficient_history",
            },
            "evidence": {
                "history_age_days": 2,
                "decision_count": 11,
                "price_evidence_count": 10,
            },
            "recommendation_scoring_mutated": False,
            "benchmark_definition_mutated": False,
            "portfolio_position_mutated": False,
            "automatic_weight_change_allowed": False,
            "automatic_rebalance_allowed": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
    }


if __name__ == "__main__":
    unittest.main()
