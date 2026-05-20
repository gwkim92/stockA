from __future__ import annotations

from datetime import datetime, timezone
import unittest

from stockanalysis.operations.scheduler_activation_decision import (
    build_data_operations_live_scheduler_activation_user_decision_report,
)


class DataOperationsSchedulerActivationDecisionTests(unittest.TestCase):
    def test_missing_decision_record_blocks_activation(self) -> None:
        report = build_data_operations_live_scheduler_activation_user_decision_report(
            activation_request_report=_activation_request_report(),
            activation_request_report_path="/tmp/stockanalysis/live-activation-request.json",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["decision_gate"], "blocked_pending_user_decision")
        self.assertFalse(report["activation_allowed_for_next_task"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])

    def test_approve_decision_allows_final_preflight_without_execution(self) -> None:
        report = build_data_operations_live_scheduler_activation_user_decision_report(
            activation_request_report=_activation_request_report(),
            decision_record=_decision_record("approve_live_scheduler_activation"),
            activation_request_report_path="/tmp/stockanalysis/live-activation-request.json",
            decision_record_path="/tmp/stockanalysis/user-decision.json",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["decision_gate"], "approved_for_live_scheduler_activation_final_preflight")
        self.assertEqual(report["user_decision"], "approve_live_scheduler_activation")
        self.assertTrue(report["activation_allowed_for_next_task"])
        self.assertFalse(report["activation_execution_allowed_in_this_task"])
        self.assertFalse(report["launchctl_executed"])
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-activation-final-preflight")

    def test_deny_decision_blocks_next_activation_task(self) -> None:
        report = build_data_operations_live_scheduler_activation_user_decision_report(
            activation_request_report=_activation_request_report(),
            decision_record=_decision_record("deny_live_scheduler_activation"),
            activation_request_report_path="/tmp/stockanalysis/live-activation-request.json",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["decision_gate"], "denied_live_scheduler_activation")
        self.assertEqual(report["user_decision"], "deny_live_scheduler_activation")
        self.assertFalse(report["activation_allowed_for_next_task"])
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-activation-request")

    def test_rejects_mismatched_request_path(self) -> None:
        decision = _decision_record("approve_live_scheduler_activation")
        decision["activation_request_report"] = "/tmp/stockanalysis/wrong-request.json"

        with self.assertRaisesRegex(ValueError, "same activation request"):
            build_data_operations_live_scheduler_activation_user_decision_report(
                activation_request_report=_activation_request_report(),
                decision_record=decision,
                activation_request_report_path="/tmp/stockanalysis/live-activation-request.json",
            )

    def test_rejects_secret_like_operator_note(self) -> None:
        decision = _decision_record("approve_live_scheduler_activation")
        decision["operator_note"] = "DATABASE_URL=postgresql://user:pass@host/db"

        with self.assertRaisesRegex(ValueError, "secret-like"):
            build_data_operations_live_scheduler_activation_user_decision_report(
                activation_request_report=_activation_request_report(),
                decision_record=decision,
                activation_request_report_path="/tmp/stockanalysis/live-activation-request.json",
            )

    def test_rejects_activation_request_that_does_not_require_user_decision(self) -> None:
        request = _activation_request_report()
        request["activation_request"] = "approved"

        with self.assertRaisesRegex(ValueError, "pending explicit user approval"):
            build_data_operations_live_scheduler_activation_user_decision_report(
                activation_request_report=request,
            )


def _activation_request_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_activation_request",
        "activation_request": "pending_explicit_user_approval",
        "requested_user_decision_values": [
            "approve_live_scheduler_activation",
            "deny_live_scheduler_activation",
        ],
        "requires_explicit_user_approval": True,
        "activation_allowed_by_gate": True,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "job_id": "macro-weekly",
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "manual_next_step": "data-operations-live-scheduler-activation-user-decision",
    }


def _decision_record(decision: str) -> dict[str, object]:
    return {
        "decision_record": "data_operations_live_scheduler_activation_user_decision",
        "decision": decision,
        "decider": "operator-handle",
        "decided_at": "2026-05-11T12:30:00Z",
        "job_id": "macro-weekly",
        "activation_request_report": "/tmp/stockanalysis/live-activation-request.json",
        "decision_scope": "data_operations_scheduler_host_activation",
        "acknowledged_request_state": "pending_explicit_user_approval",
        "acknowledged_mutation_boundary": [
            "host_launchagents_write",
            "launchctl_bootstrap",
            "recurring_data_operation_execution",
            "rollback_required_if_activation_fails",
        ],
        "operator_note": "fixture decision record",
    }


if __name__ == "__main__":
    unittest.main()
