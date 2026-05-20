from __future__ import annotations

from datetime import datetime, timezone
import unittest

from stockanalysis.operations.manual_host_scheduler_activation_approval import (
    build_manual_host_scheduler_activation_explicit_approval_report,
)


class ManualHostSchedulerActivationApprovalTests(unittest.TestCase):
    def test_missing_approval_blocks_host_mutation_and_emits_template(self) -> None:
        report = build_manual_host_scheduler_activation_explicit_approval_report(
            host_activation_execution_report=_host_activation_execution_report(),
            host_activation_execution_report_path="/tmp/data-ops-manual-approval/host-activation-execution.json",
            generated_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        )

        self.assertEqual(report["approval_gate"], "blocked_pending_exact_host_command_approval")
        self.assertFalse(report["host_activation_allowed_for_manual_operator"])
        self.assertFalse(report["codex_host_mutation_allowed"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertEqual(report["manual_next_step"], "manual-host-scheduler-activation-explicit-approval")
        self.assertEqual(
            report["approval_record_template"]["approved_exact_execution_commands"],
            _execution_commands(),
        )

    def test_approval_allows_manual_operator_only_without_codex_execution(self) -> None:
        report = build_manual_host_scheduler_activation_explicit_approval_report(
            host_activation_execution_report=_host_activation_execution_report(),
            approval_record=_approval_record("approve_exact_host_scheduler_activation"),
            host_activation_execution_report_path="/tmp/data-ops-manual-approval/host-activation-execution.json",
            approval_record_path="/tmp/data-ops-manual-approval/approval.json",
        )

        self.assertEqual(report["approval_gate"], "approved_for_manual_operator_host_activation_not_executed_by_codex")
        self.assertTrue(report["host_activation_allowed_for_manual_operator"])
        self.assertFalse(report["codex_host_mutation_allowed"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertFalse(report["host_activation_execution_performed"])
        self.assertEqual(report["manual_next_step"], "manual-host-scheduler-activation-operator-evidence")

    def test_abort_approval_blocks_manual_host_mutation(self) -> None:
        report = build_manual_host_scheduler_activation_explicit_approval_report(
            host_activation_execution_report=_host_activation_execution_report(),
            approval_record=_approval_record("abort_exact_host_scheduler_activation"),
            host_activation_execution_report_path="/tmp/data-ops-manual-approval/host-activation-execution.json",
        )

        self.assertEqual(report["approval_gate"], "aborted_manual_host_scheduler_activation")
        self.assertFalse(report["host_activation_allowed_for_manual_operator"])
        self.assertEqual(
            report["manual_next_step"],
            "data-operations-live-scheduler-host-activation-execution-final-preflight",
        )

    def test_rejects_unconfirmed_host_activation_execution_report(self) -> None:
        host_report = _host_activation_execution_report()
        host_report["execution_gate"] = "blocked_pending_explicit_host_mutation_confirmation"
        host_report["host_activation_execution_allowed_for_manual_operator"] = False

        with self.assertRaisesRegex(ValueError, "confirmed for manual host mutation"):
            build_manual_host_scheduler_activation_explicit_approval_report(
                host_activation_execution_report=host_report,
            )

    def test_rejects_exact_command_drift(self) -> None:
        approval = _approval_record("approve_exact_host_scheduler_activation")
        approval["approved_exact_execution_commands"] = ["launchctl bootstrap gui/501 /tmp/wrong.plist"]

        with self.assertRaisesRegex(ValueError, "exact execution commands"):
            build_manual_host_scheduler_activation_explicit_approval_report(
                host_activation_execution_report=_host_activation_execution_report(),
                approval_record=approval,
                host_activation_execution_report_path="/tmp/data-ops-manual-approval/host-activation-execution.json",
            )

    def test_rejects_secret_like_operator_note(self) -> None:
        approval = _approval_record("approve_exact_host_scheduler_activation")
        approval["operator_note"] = "postgresql://user:pass@host/db"

        with self.assertRaisesRegex(ValueError, "secret-like"):
            build_manual_host_scheduler_activation_explicit_approval_report(
                host_activation_execution_report=_host_activation_execution_report(),
                approval_record=approval,
                host_activation_execution_report_path="/tmp/data-ops-manual-approval/host-activation-execution.json",
            )


def _host_activation_execution_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_host_activation_execution",
        "execution_gate": "confirmed_for_manual_host_mutation_not_executed_by_this_task",
        "host_activation_execution_allowed_in_this_task": False,
        "host_activation_execution_allowed_for_manual_operator": True,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_performed": False,
        "job_id": "macro-weekly",
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "rendered_label": "com.stockanalysis.data-operations.macro-weekly",
        "host_plist_path_preview": "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist",
        "execution_command_preview": _execution_commands(),
        "rollback_command_preview": _rollback_commands(),
        "manual_next_step": "manual-host-scheduler-activation",
    }


def _approval_record(approval: str) -> dict[str, object]:
    return {
        "approval_record": "manual_host_scheduler_activation_explicit_approval",
        "approval": approval,
        "approver": "operator-handle",
        "approved_at": "2026-05-15T09:30:00Z",
        "job_id": "macro-weekly",
        "host_activation_execution_report": "/tmp/data-ops-manual-approval/host-activation-execution.json",
        "approval_scope": "manual_host_scheduler_activation",
        "acknowledged_execution_gate": "confirmed_for_manual_host_mutation_not_executed_by_this_task",
        "approved_exact_execution_commands": _execution_commands(),
        "approved_exact_rollback_commands": _rollback_commands(),
        "acknowledged_mutation_boundary": [
            "host_launchagents_write",
            "launchctl_bootstrap",
            "launchctl_kickstart",
            "launchctl_print",
            "rollback_required_if_activation_fails",
            "recurring_data_operation_execution",
        ],
        "acknowledged_operator_responsibility": [
            "operator_runs_commands_outside_codex",
            "operator_records_exit_statuses",
            "operator_collects_launchctl_print_evidence",
            "operator_collects_first_run_artifacts",
            "operator_can_execute_rollback",
        ],
        "operator_note": "fixture approval",
    }


def _execution_commands() -> list[str]:
    return [
        'install -m 600 "/tmp/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        'launchctl kickstart -k "gui/$(id -u)/com.stockanalysis.data-operations.macro-weekly"',
        'launchctl print "gui/$(id -u)/com.stockanalysis.data-operations.macro-weekly"',
    ]


def _rollback_commands() -> list[str]:
    return [
        'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        'launchctl print "gui/$(id -u)/com.stockanalysis.data-operations.macro-weekly"',
    ]


if __name__ == "__main__":
    unittest.main()
