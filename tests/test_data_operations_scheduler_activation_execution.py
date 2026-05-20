from __future__ import annotations

from datetime import datetime, timezone
import unittest

from stockanalysis.operations.scheduler_activation_execution import (
    build_data_operations_live_scheduler_host_activation_execution_report,
)


class DataOperationsSchedulerActivationExecutionTests(unittest.TestCase):
    def test_missing_confirmation_blocks_host_mutation(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_execution_report(
            execution_final_preflight_report=_execution_final_preflight_report(),
            execution_final_preflight_report_path="/tmp/data-ops-host-execution/execution-final-preflight.json",
            generated_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        )

        self.assertEqual(report["execution_gate"], "blocked_pending_explicit_host_mutation_confirmation")
        self.assertFalse(report["host_activation_execution_allowed_in_this_task"])
        self.assertFalse(report["host_activation_execution_allowed_for_manual_operator"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-host-activation-execution")

    def test_confirmation_allows_manual_operator_only_without_execution(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_execution_report(
            execution_final_preflight_report=_execution_final_preflight_report(),
            confirmation_record=_confirmation_record("confirm_host_activation_execution"),
            execution_final_preflight_report_path="/tmp/data-ops-host-execution/execution-final-preflight.json",
            confirmation_record_path="/tmp/data-ops-host-execution/confirm.json",
        )

        self.assertEqual(report["execution_gate"], "confirmed_for_manual_host_mutation_not_executed_by_this_task")
        self.assertFalse(report["host_activation_execution_allowed_in_this_task"])
        self.assertTrue(report["host_activation_execution_allowed_for_manual_operator"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertFalse(report["host_activation_execution_performed"])
        self.assertEqual(report["manual_next_step"], "manual-host-scheduler-activation")

    def test_abort_confirmation_blocks_execution(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_execution_report(
            execution_final_preflight_report=_execution_final_preflight_report(),
            confirmation_record=_confirmation_record("abort_host_activation_execution"),
            execution_final_preflight_report_path="/tmp/data-ops-host-execution/execution-final-preflight.json",
        )

        self.assertEqual(report["execution_gate"], "aborted_by_explicit_host_mutation_confirmation")
        self.assertFalse(report["host_activation_execution_allowed_for_manual_operator"])
        self.assertEqual(
            report["manual_next_step"],
            "data-operations-live-scheduler-host-activation-execution-final-preflight",
        )

    def test_rejects_non_passing_final_preflight(self) -> None:
        preflight = _execution_final_preflight_report()
        preflight["execution_final_preflight"] = "blocked_runtime_env_not_ready"
        preflight["host_activation_execution_allowed_for_next_task"] = False

        with self.assertRaisesRegex(ValueError, "passed_ready_for_host_activation_execution_task"):
            build_data_operations_live_scheduler_host_activation_execution_report(
                execution_final_preflight_report=preflight,
            )

    def test_rejects_confirmation_path_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "same execution final preflight report path"):
            build_data_operations_live_scheduler_host_activation_execution_report(
                execution_final_preflight_report=_execution_final_preflight_report(),
                confirmation_record=_confirmation_record("confirm_host_activation_execution"),
                execution_final_preflight_report_path="/tmp/data-ops-host-execution/wrong.json",
            )

    def test_rejects_secret_like_operator_note(self) -> None:
        confirmation = _confirmation_record("confirm_host_activation_execution")
        confirmation["operator_note"] = "postgresql://user:pass@host/db"

        with self.assertRaisesRegex(ValueError, "secret-like"):
            build_data_operations_live_scheduler_host_activation_execution_report(
                execution_final_preflight_report=_execution_final_preflight_report(),
                confirmation_record=confirmation,
                execution_final_preflight_report_path="/tmp/data-ops-host-execution/execution-final-preflight.json",
            )


def _execution_final_preflight_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_host_activation_execution_final_preflight",
        "execution_final_preflight": "passed_ready_for_host_activation_execution_task",
        "host_activation_execution_allowed_for_next_task": True,
        "host_activation_execution_allowed_in_this_task": False,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "job_id": "macro-weekly",
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "rendered_label": "com.stockanalysis.data-operations.macro-weekly",
        "host_plist_path_preview": "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist",
        "execution_command_preview": [
            'install -m 600 "/tmp/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
        "rollback_command_preview": [
            'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
        "manual_next_step": "data-operations-live-scheduler-host-activation-execution",
    }


def _confirmation_record(confirmation: str) -> dict[str, object]:
    return {
        "confirmation_record": "data_operations_live_scheduler_host_activation_execution_confirmation",
        "confirmation": confirmation,
        "confirmer": "operator-handle",
        "confirmed_at": "2026-05-15T09:00:00Z",
        "job_id": "macro-weekly",
        "execution_final_preflight_report": "/tmp/data-ops-host-execution/execution-final-preflight.json",
        "confirmation_scope": "data_operations_scheduler_host_activation_execution",
        "acknowledged_final_preflight_state": "passed_ready_for_host_activation_execution_task",
        "acknowledged_mutation_boundary": [
            "host_launchagents_write",
            "launchctl_bootstrap",
            "launchctl_kickstart",
            "launchctl_print",
            "rollback_required_if_activation_fails",
            "recurring_data_operation_execution",
        ],
        "operator_note": "fixture confirmation",
    }


if __name__ == "__main__":
    unittest.main()
