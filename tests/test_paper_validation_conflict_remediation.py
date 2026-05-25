from __future__ import annotations

import json
import unittest
from datetime import date

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.operations.paper_validation_conflict_remediation import (
    classify_paper_validation_conflicts,
    render_paper_validation_conflict_remediation_sql,
    run_paper_validation_conflict_remediation,
)


class FakePaperValidationConflictExecutor:
    def __init__(self, *, run_id: int = 9801) -> None:
        self.run_id = run_id
        self.scalar_sql: list[str] = []
        self.non_query_sql: list[str] = []

    def execute_scalar(self, sql: str) -> str:
        self.scalar_sql.append(sql)
        if sql.startswith("-- paper validation conflict remediation lookup"):
            return json.dumps(_payload())
        if "insert into ops.pipeline_run" in sql:
            return str(self.run_id)
        raise AssertionError(f"Unexpected scalar SQL: {sql[:120]}")

    def execute_non_query(self, sql: str) -> None:
        self.non_query_sql.append(sql)


class PaperValidationConflictRemediationTests(unittest.TestCase):
    def test_render_lookup_sql_is_read_only_and_targets_latest_validation(self) -> None:
        sql = render_paper_validation_conflict_remediation_sql(
            as_of_date=date(2026, 5, 25),
            portfolio_name="Long Term Paper",
        )
        lowered = sql.lower()

        self.assertIn("-- paper validation conflict remediation lookup", sql)
        self.assertIn("trading.paper_validation_run", sql)
        self.assertIn("trading.order_intent_audit", sql)
        self.assertIn("'2026-05-25'::date", sql)
        self.assertNotIn("insert into", lowered)
        self.assertNotIn("update ", lowered)
        self.assertNotIn("delete from", lowered)

    def test_classify_separates_portfolio_gaps_from_safety_interlocks(self) -> None:
        classification = classify_paper_validation_conflicts(_payload())

        self.assertEqual(classification["decision"], "blocked_by_portfolio_recommendation_coverage_gap")
        self.assertFalse(classification["weight_review_allowed"])
        self.assertFalse(classification["automatic_order_allowed"])
        self.assertFalse(classification["broker_submit_allowed"])
        self.assertEqual(classification["summary"]["portfolio_coverage_issue_count"], 3)
        self.assertEqual(classification["summary"]["non_actionable_zero_delta_issue_count"], 3)
        self.assertEqual(classification["summary"]["safety_interlock_issue_count"], 4)
        issues_by_symbol = {str(item["symbol"]): item for item in classification["issues"]}
        self.assertEqual(issues_by_symbol["AAPL"]["issue_type"], "portfolio_recommendation_coverage_gap")
        self.assertEqual(issues_by_symbol["AAPL"]["order_delta_status"], "zero_delta_review_only")
        self.assertIn("skipped:AAPL:target_weight_equals_current_weight", issues_by_symbol["AAPL"]["raw_reasons"])
        self.assertEqual(issues_by_symbol["AEIS"]["issue_type"], "safety_interlock")
        self.assertIn("kill_switch_engaged", issues_by_symbol["AEIS"]["reason_codes"])

    def test_run_dry_run_does_not_write_pipeline_run(self) -> None:
        executor = FakePaperValidationConflictExecutor()

        report = run_paper_validation_conflict_remediation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            execute=False,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "planned")
        self.assertEqual(report["classification"]["decision"], "blocked_by_portfolio_recommendation_coverage_gap")
        self.assertEqual(len(executor.scalar_sql), 1)
        self.assertEqual(executor.non_query_sql, [])

    def test_run_execute_records_pipeline_without_changing_recommendations(self) -> None:
        executor = FakePaperValidationConflictExecutor(run_id=9802)

        report = run_paper_validation_conflict_remediation(
            config=RuntimeConfig(psql_command="psql"),
            as_of_date=date(2026, 5, 25),
            execute=True,
            executor=executor,  # type: ignore[arg-type]
        )

        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["run_id"], 9802)
        self.assertIn("insert into ops.pipeline_run", executor.scalar_sql[1])
        self.assertIn("status = 'succeeded'", executor.non_query_sql[-1])
        combined_sql = "\n".join(executor.scalar_sql + executor.non_query_sql).lower()
        self.assertNotIn("update signal.recommendation", combined_sql)
        self.assertNotIn("insert into trading.order_intent_audit", combined_sql)


def _payload() -> dict[str, object]:
    return {
        "as_of_date": "2026-05-25",
        "portfolio_name": "Long Term Paper",
        "paper_validation": {
            "paper_validation_run_id": 9,
            "validation_date": "2026-05-25",
            "status": "failed",
            "recommendation_count": 6,
            "conflict_count": 3,
            "approved_action_count": 0,
            "blocked_reasons": [
                "position_recommendation_conflict:AAPL",
                "skipped:AAPL:target_weight_equals_current_weight",
                "position_recommendation_conflict:MSFT",
                "skipped:MSFT:target_weight_equals_current_weight",
                "position_recommendation_conflict:TSLA",
                "skipped:TSLA:target_weight_equals_current_weight",
                "AEIS:kill_switch_engaged",
                "AEIS:human_approval_required",
                "ARM:kill_switch_engaged",
                "ARM:human_approval_required",
                "QUBT:kill_switch_engaged",
                "QUBT:human_approval_required",
                "SPY:kill_switch_engaged",
                "SPY:human_approval_required",
            ],
        },
        "order_intent_audits": [],
    }


if __name__ == "__main__":
    unittest.main()
