from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.operations.recommendation_outcome_due_action_router import (
    DEFAULT_DATASET_VERSION,
    DEFAULT_EVAL_NAME,
    build_recommendation_outcome_due_action_router_decision,
    render_recommendation_outcome_due_action_router_context_sql,
    render_recommendation_outcome_due_action_router_insert_sql,
    run_recommendation_outcome_due_action_router,
)


class FakeOutcomeDueActionRouterExecutor:
    def __init__(self, *, latest_calibration: dict[str, object], sample_audit: dict[str, object]) -> None:
        self.latest_calibration = latest_calibration
        self.sample_audit = sample_audit
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if sql.startswith("-- recommendation outcome due action router context lookup"):
            return json.dumps(self.latest_calibration)
        if sql.startswith("-- recommendation outcome calibration sample audit lookup"):
            return json.dumps(self.sample_audit)
        if "insert into ops.pipeline_run" in lowered:
            return "9701"
        if "insert into ai.eval_run" in lowered:
            return "8701"
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class RecommendationOutcomeDueActionRouterTests(unittest.TestCase):
    def test_ready_backfill_routes_to_calibration_runner(self) -> None:
        action = build_recommendation_outcome_due_action_router_decision(
            context=_context(sample_audit=_sample_audit(ready=3)),
            as_of_date=date(2026, 6, 20),
            horizon_days=(30,),
        )

        self.assertEqual(action["route_action"], "execute_calibration")
        self.assertEqual(action["action_status"], "execute_outcome_calibration_ready")
        self.assertEqual(action["sample_audit_summary"]["ready_for_backfill_count"], 3)  # type: ignore[index]
        self.assertFalse(action["automatic_weight_change_allowed"])
        self.assertFalse(action["broker_submit_allowed"])

    def test_price_gaps_block_calibration_without_child_runner(self) -> None:
        action = build_recommendation_outcome_due_action_router_decision(
            context=_context(sample_audit=_sample_audit(ready=0, missing_exit=2)),
            as_of_date=date(2026, 6, 20),
            horizon_days=(30,),
        )

        self.assertEqual(action["route_action"], "no_op")
        self.assertEqual(action["action_status"], "blocked_by_price_gaps")
        self.assertIn("가격 이력", action["reason"])

    def test_not_due_waits_until_next_measurement_date(self) -> None:
        action = build_recommendation_outcome_due_action_router_decision(
            context=_context(sample_audit=_sample_audit(ready=0, not_due=4)),
            as_of_date=date(2026, 5, 27),
            horizon_days=(30,),
        )

        self.assertEqual(action["route_action"], "no_op")
        self.assertEqual(action["action_status"], "no_op_wait_until_next_due_date")
        self.assertEqual(action["wait_until"], "2026-06-20")

    def test_guardrail_violation_blocks_supported_runner(self) -> None:
        latest = _latest_calibration()
        latest["score_json"]["broker_submit_allowed"] = True  # type: ignore[index]
        action = build_recommendation_outcome_due_action_router_decision(
            context=_context(latest_calibration=latest, sample_audit=_sample_audit(ready=2)),
            as_of_date=date(2026, 6, 20),
            horizon_days=(30,),
        )

        self.assertEqual(action["route_action"], "no_op")
        self.assertEqual(action["action_status"], "blocked_guardrail_violation")

    def test_sql_renderers_are_read_only_except_action_audit_insert(self) -> None:
        lookup_sql = render_recommendation_outcome_due_action_router_context_sql(as_of_date=date(2026, 5, 27))
        insert_sql = render_recommendation_outcome_due_action_router_insert_sql(
            score_json={"action_status": "no_op_wait_until_next_due_date"}
        )
        lowered_lookup = lookup_sql.lower()
        lowered_insert = insert_sql.lower()

        self.assertIn("from ai.eval_run", lookup_sql)
        self.assertIn("recommendation_outcome_calibration_sample_expansion", lookup_sql)
        self.assertNotIn("insert into", lowered_lookup)
        self.assertNotIn("update ", lowered_lookup)
        self.assertNotIn("delete from", lowered_lookup)
        self.assertIn("insert into ai.eval_run", lowered_insert)
        self.assertIn(DEFAULT_EVAL_NAME, insert_sql)
        self.assertIn(DEFAULT_DATASET_VERSION, insert_sql)
        self.assertNotIn("signal.recommendation_score_component", lowered_insert)
        self.assertNotIn("broker", lowered_insert)

    def test_run_execute_ready_invokes_calibration_runner_and_records_audit(self) -> None:
        executor = FakeOutcomeDueActionRouterExecutor(
            latest_calibration=_latest_calibration(),
            sample_audit=_sample_audit(ready=2),
        )
        calls: list[dict[str, object]] = []

        def calibration_runner(**kwargs: object) -> dict[str, object]:
            calls.append(kwargs)
            return {
                "report_name": "recommendation_outcome_calibration_sample_expansion",
                "status": "completed",
                "run_id": 9801,
                "eval_run_id": 8801,
                "score": {
                    "status": "collect_more_outcomes_keep_weights",
                    "quality_status": "collect_more_outcomes",
                    "sample_status": "insufficient_sample",
                },
            }

        report = run_recommendation_outcome_due_action_router(
            config=type("Config", (), {"psql_command": "psql"})(),
            as_of_date=date(2026, 6, 20),
            horizon_days=(30,),
            execute=True,
            executor=executor,
            calibration_runner=calibration_runner,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9701)
        self.assertEqual(report["eval_run_id"], 8701)
        self.assertEqual(report["action"]["action_status"], "outcome_calibration_executed")  # type: ignore[index]
        self.assertTrue(report["action"]["child_runner"]["executed"])  # type: ignore[index]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["execute"], True)
        self.assertEqual(calls[0]["horizon_days"], (30,))
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[-1].lower())
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])

    def test_run_execute_no_op_records_audit_without_child_runner(self) -> None:
        executor = FakeOutcomeDueActionRouterExecutor(
            latest_calibration=_latest_calibration(),
            sample_audit=_sample_audit(ready=0, not_due=4),
        )
        calls: list[dict[str, object]] = []

        report = run_recommendation_outcome_due_action_router(
            config=type("Config", (), {"psql_command": "psql"})(),
            as_of_date=date(2026, 5, 27),
            horizon_days=(30,),
            execute=True,
            executor=executor,
            calibration_runner=lambda **kwargs: calls.append(kwargs) or {},
        )

        self.assertEqual(report["action"]["action_status"], "no_op_wait_until_next_due_date")  # type: ignore[index]
        self.assertFalse(report["action"]["child_runner"]["executed"])  # type: ignore[index]
        self.assertEqual(calls, [])


def _context(
    *,
    latest_calibration: dict[str, object] | None = None,
    sample_audit: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "latest_calibration": latest_calibration or _latest_calibration(),
        "sample_audit": sample_audit or _sample_audit(),
    }


def _latest_calibration() -> dict[str, object]:
    return {
        "status": "loaded",
        "eval_run_id": 27,
        "created_at": "2026-05-27T08:00:00+00:00",
        "score_json": {
            "as_of_date": "2026-05-27",
            "status": "no_due_outcome_window",
            "quality_status": "insufficient_sample",
            "sample_status": "not_due",
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "order_boundary": "read_only_no_order",
        },
    }


def _sample_audit(
    *,
    ready: int = 0,
    not_due: int = 0,
    missing_entry: int = 0,
    missing_exit: int = 0,
    outcome_count: int = 0,
) -> dict[str, object]:
    total = ready + not_due + missing_entry + missing_exit + outcome_count
    examples = []
    if not_due:
        examples.append(
            {
                "primary_symbol": "AAPL",
                "recommendation_id": 147,
                "as_of_date": "2026-05-21",
                "horizon_day": 30,
                "expected_measurement_end_date": "2026-06-20",
                "sample_status": "not_due",
                "benchmark_warning": None,
            }
        )
    return {
        "summary": {
            "recommendation_horizon_count": total,
            "recommendation_count": total,
            "outcome_count": outcome_count,
            "ready_for_backfill_count": ready,
            "not_due_count": not_due,
            "missing_entry_price_count": missing_entry,
            "missing_exit_price_count": missing_exit,
            "benchmark_warning_count": 0,
            "outcome_coverage_rate": 0 if total == 0 else outcome_count / total,
        },
        "horizon_coverage": [
            {
                "horizon_day": 30,
                "recommendation_horizon_count": total,
                "outcome_count": outcome_count,
                "ready_for_backfill_count": ready,
                "not_due_count": not_due,
                "price_gap_count": missing_entry + missing_exit,
            }
        ],
        "missing_reason_counts": {
            "ready_for_backfill": ready,
            "not_due": not_due,
            "missing_entry_price": missing_entry,
            "missing_exit_price": missing_exit,
        },
        "missing_examples": examples,
        "guardrails": {
            "recommendation_scoring_mutated": False,
            "automatic_order_allowed": False,
            "broker_submit_allowed": False,
            "outcome_policy": "price_based_outcomes_only_no_synthetic_returns",
        },
    }


if __name__ == "__main__":
    unittest.main()

