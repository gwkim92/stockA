from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.operations.portfolio_review_feedback_calibration import (
    DEFAULT_DATASET_VERSION,
    DEFAULT_EVAL_NAME,
    build_portfolio_review_feedback_calibration,
    render_portfolio_review_feedback_artifacts_lookup_sql,
    render_portfolio_review_feedback_calibration_insert_sql,
    run_portfolio_review_feedback_calibration,
)


class FakeCalibrationExecutor:
    def __init__(self, feedback_artifacts: list[dict[str, object]]) -> None:
        self.feedback_artifacts = feedback_artifacts
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        lowered = sql.lower()
        if sql.startswith("-- portfolio review feedback calibration artifacts lookup"):
            return json.dumps(self.feedback_artifacts)
        if "insert into ops.pipeline_run" in lowered:
            return "9301"
        if "insert into ai.eval_run" in lowered:
            return "8301"
        raise AssertionError(f"Unexpected scalar SQL: {sql}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PortfolioReviewFeedbackCalibrationTests(unittest.TestCase):
    def test_build_marks_single_young_feedback_as_insufficient_history(self) -> None:
        calibration = build_portfolio_review_feedback_calibration(
            feedback_artifacts=[
                _feedback_artifact(
                    eval_run_id=53,
                    as_of_date="2026-05-27",
                    items=[_feedback_item(symbol="TSLA", feedback_status="too_early")],
                )
            ],
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )

        self.assertEqual(calibration["eval_name"], DEFAULT_EVAL_NAME)
        self.assertEqual(calibration["dataset_version"], DEFAULT_DATASET_VERSION)
        self.assertEqual(calibration["calibration_status"], "insufficient_history")
        self.assertEqual(calibration["feedback_run_count"], 1)
        self.assertEqual(calibration["decision_count"], 1)
        self.assertEqual(calibration["too_early_count"], 1)
        self.assertFalse(calibration["guardrails"]["automatic_order_allowed"])
        self.assertFalse(calibration["guardrails"]["broker_submit_allowed"])

    def test_build_flags_high_contradiction_rate_for_manual_review(self) -> None:
        calibration = build_portfolio_review_feedback_calibration(
            feedback_artifacts=[
                _feedback_artifact(
                    eval_run_id=run_id,
                    as_of_date=f"2026-05-{20 + run_id}",
                    items=[
                        _feedback_item(symbol="TSLA", feedback_status="contradicted"),
                        _feedback_item(symbol="MSFT", feedback_status="validated"),
                        _feedback_item(symbol="AAPL", feedback_status="validated"),
                        _feedback_item(symbol="NVDA", feedback_status="validated"),
                    ],
                )
                for run_id in range(1, 4)
            ],
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            min_feedback_runs=3,
            min_mature_decisions=10,
            max_contradiction_rate=0.15,
        )

        self.assertEqual(calibration["calibration_status"], "contradiction_review_required")
        self.assertEqual(calibration["mature_decision_count"], 12)
        self.assertEqual(calibration["contradicted_count"], 3)
        self.assertEqual(calibration["contradiction_rate"], 0.25)
        self.assertEqual(calibration["symbol_summaries"][0]["symbol"], "TSLA")

    def test_build_allows_manual_review_ready_only_after_mature_clean_history(self) -> None:
        calibration = build_portfolio_review_feedback_calibration(
            feedback_artifacts=[
                _feedback_artifact(
                    eval_run_id=run_id,
                    as_of_date=f"2026-05-{20 + run_id}",
                    items=[
                        _feedback_item(symbol="TSLA", feedback_status="validated"),
                        _feedback_item(symbol="MSFT", feedback_status="validated"),
                        _feedback_item(symbol="AAPL", feedback_status="validated"),
                        _feedback_item(symbol="NVDA", feedback_status="validated"),
                    ],
                )
                for run_id in range(1, 4)
            ],
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            min_feedback_runs=3,
            min_mature_decisions=10,
            max_contradiction_rate=0.15,
        )

        self.assertEqual(calibration["calibration_status"], "manual_review_ready")
        self.assertEqual(calibration["mature_decision_count"], 12)
        self.assertEqual(calibration["validated_count"], 12)
        self.assertEqual(calibration["contradicted_count"], 0)
        self.assertIn("자동 weight 변경은 여전히 금지", calibration["next_action"])

    def test_sql_renderers_keep_calibration_audit_only(self) -> None:
        lookup_sql = render_portfolio_review_feedback_artifacts_lookup_sql(
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
        )
        insert_sql = render_portfolio_review_feedback_calibration_insert_sql(
            score_json={"calibration_status": "insufficient_history"}
        )
        lowered_lookup = lookup_sql.lower()
        lowered_insert = insert_sql.lower()

        self.assertIn("from ai.eval_run", lowered_lookup)
        self.assertIn("portfolio_review_decision_outcome_feedback", lookup_sql)
        self.assertNotIn("insert into", lowered_lookup)
        self.assertNotIn("update ", lowered_lookup)
        self.assertNotIn("delete from", lowered_lookup)
        self.assertIn("insert into ai.eval_run", lowered_insert)
        self.assertIn(DEFAULT_EVAL_NAME, insert_sql)
        self.assertIn(DEFAULT_DATASET_VERSION, insert_sql)
        self.assertNotIn("signal.recommendation_score_component", lowered_insert)
        self.assertNotIn("portfolio.position_snapshot", lowered_insert)
        self.assertNotIn("from broker", lowered_insert)
        self.assertNotIn("join broker", lowered_insert)

    def test_run_execute_records_pipeline_and_eval_run(self) -> None:
        executor = FakeCalibrationExecutor(
            [
                _feedback_artifact(
                    eval_run_id=53,
                    as_of_date="2026-05-27",
                    items=[_feedback_item(symbol="TSLA", feedback_status="too_early")],
                )
            ]
        )

        report = run_portfolio_review_feedback_calibration(
            config=type("Config", (), {"psql_command": "psql"})(),
            portfolio_name="Long Term Paper",
            as_of_date=date(2026, 5, 27),
            execute=True,
            executor=executor,
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9301)
        self.assertEqual(report["eval_run_id"], 8301)
        self.assertIn("portfolio review feedback calibration artifacts lookup", executor.scalar_sql[0])
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1].lower())
        self.assertIn("insert into ai.eval_run", executor.scalar_sql[2].lower())
        self.assertIn("status = 'succeeded'", executor.non_query_sql[0])


def _feedback_artifact(*, eval_run_id: int, as_of_date: str, items: list[dict[str, object]]) -> dict[str, object]:
    return {
        "eval_run_id": eval_run_id,
        "created_at": f"{as_of_date}T03:00:00+00:00",
        "score_json": {
            "as_of_date": as_of_date,
            "portfolio_name": "Long Term Paper",
            "feedback_status": "has_contradictions"
            if any(item.get("feedback_status") == "contradicted" for item in items)
            else "too_early"
            if any(item.get("feedback_status") == "too_early" for item in items)
            else "validated",
            "decision_count": len(items),
            "too_early_count": sum(1 for item in items if item.get("feedback_status") == "too_early"),
            "validated_count": sum(1 for item in items if item.get("feedback_status") == "validated"),
            "contradicted_count": sum(1 for item in items if item.get("feedback_status") == "contradicted"),
            "needs_more_data_count": sum(1 for item in items if item.get("feedback_status") == "needs_more_data"),
            "latest_items": items,
        },
    }


def _feedback_item(
    *,
    symbol: str,
    feedback_status: str,
    decision_family: str = "benchmark_drift",
    decision_type: str = "reduce_watch",
) -> dict[str, object]:
    return {
        "decision_family": decision_family,
        "symbol": symbol,
        "decision_type": decision_type,
        "feedback_status": feedback_status,
    }


if __name__ == "__main__":
    unittest.main()
