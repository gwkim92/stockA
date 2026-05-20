from __future__ import annotations

from datetime import datetime, timezone
import unittest

from stockanalysis.operations.scheduler_activation_execution_decision import (
    build_data_operations_live_scheduler_host_activation_execution_decision_report,
)


class DataOperationsSchedulerActivationExecutionDecisionTests(unittest.TestCase):
    def test_missing_decision_blocks_execution(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_execution_decision_report(
            execution_request_report=_execution_request_report(),
            execution_request_report_path="/tmp/data-ops-execution-decision/execution-request.json",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["decision_gate"], "blocked_pending_execution_decision")
        self.assertEqual(report["user_decision"], "missing")
        self.assertFalse(report["host_activation_execution_allowed_for_next_task"])
        self.assertFalse(report["host_activation_execution_allowed_in_this_task"])
        self.assertFalse(report["launchctl_executed"])
        self.assertEqual(
            report["manual_next_step"],
            "data-operations-live-scheduler-host-activation-execution-decision",
        )

    def test_approve_decision_allows_final_preflight_without_execution(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_execution_decision_report(
            execution_request_report=_execution_request_report(),
            decision_record=_decision_record("approve_host_activation_execution"),
            execution_request_report_path="/tmp/data-ops-execution-decision/execution-request.json",
            decision_record_path="/tmp/data-ops-execution-decision/approve-decision.json",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["decision_gate"], "approved_for_host_activation_execution_final_preflight")
        self.assertEqual(report["user_decision"], "approve_host_activation_execution")
        self.assertTrue(report["host_activation_execution_allowed_for_next_task"])
        self.assertFalse(report["host_activation_execution_allowed_in_this_task"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertEqual(
            report["manual_next_step"],
            "data-operations-live-scheduler-host-activation-execution-final-preflight",
        )

    def test_deny_decision_blocks_execution(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_execution_decision_report(
            execution_request_report=_execution_request_report(),
            decision_record=_decision_record("deny_host_activation_execution"),
            execution_request_report_path="/tmp/data-ops-execution-decision/execution-request.json",
        )

        self.assertEqual(report["decision_gate"], "denied_host_activation_execution")
        self.assertEqual(report["user_decision"], "deny_host_activation_execution")
        self.assertFalse(report["host_activation_execution_allowed_for_next_task"])
        self.assertEqual(
            report["manual_next_step"],
            "data-operations-live-scheduler-host-activation-execution-request",
        )

    def test_rejects_execution_request_that_does_not_require_decision(self) -> None:
        request = _execution_request_report()
        request["execution_request"] = "not_pending"
        request["requires_explicit_execution_approval"] = False

        with self.assertRaisesRegex(ValueError, "pending_explicit_execution_approval"):
            build_data_operations_live_scheduler_host_activation_execution_decision_report(
                execution_request_report=request,
            )

    def test_rejects_mismatched_request_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "same execution request report path"):
            build_data_operations_live_scheduler_host_activation_execution_decision_report(
                execution_request_report=_execution_request_report(),
                decision_record=_decision_record("approve_host_activation_execution"),
                execution_request_report_path="/tmp/data-ops-execution-decision/wrong-request.json",
            )

    def test_rejects_secret_like_operator_note(self) -> None:
        decision = _decision_record("approve_host_activation_execution")
        decision["operator_note"] = "postgresql://user:pass@host/db"

        with self.assertRaisesRegex(ValueError, "secret-like"):
            build_data_operations_live_scheduler_host_activation_execution_decision_report(
                execution_request_report=_execution_request_report(),
                decision_record=decision,
                execution_request_report_path="/tmp/data-ops-execution-decision/execution-request.json",
            )


def _execution_request_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_host_activation_execution_request",
        "execution_request": "pending_explicit_execution_approval",
        "requested_user_decision_values": [
            "approve_host_activation_execution",
            "deny_host_activation_execution",
        ],
        "requires_explicit_execution_approval": True,
        "execution_allowed_by_plan": True,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_allowed_in_this_task": False,
        "job_id": "macro-weekly",
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "execution_command_preview": [
            'install -m 600 "/tmp/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
        "rollback_command_preview": [
            'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
        "manual_next_step": "data-operations-live-scheduler-host-activation-execution-decision",
    }


def _decision_record(decision: str) -> dict[str, object]:
    return {
        "decision_record": "data_operations_live_scheduler_host_activation_execution_decision",
        "decision": decision,
        "decider": "operator-handle",
        "decided_at": "2026-05-11T13:00:00Z",
        "job_id": "macro-weekly",
        "execution_request_report": "/tmp/data-ops-execution-decision/execution-request.json",
        "decision_scope": "data_operations_scheduler_host_activation_execution",
        "acknowledged_request_state": "pending_explicit_execution_approval",
        "acknowledged_mutation_boundary": [
            "host_launchagents_write",
            "launchctl_bootstrap",
            "launchctl_kickstart",
            "launchctl_print",
            "rollback_required_if_activation_fails",
            "recurring_data_operation_execution",
        ],
        "operator_note": "fixture execution decision",
    }


if __name__ == "__main__":
    unittest.main()
