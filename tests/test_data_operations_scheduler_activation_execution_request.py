from __future__ import annotations

from datetime import datetime, timezone
import unittest

from stockanalysis.operations.scheduler_activation_execution_request import (
    build_data_operations_live_scheduler_host_activation_execution_request_report,
)


class DataOperationsSchedulerActivationExecutionRequestTests(unittest.TestCase):
    def test_builds_pending_execution_request_without_execution(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_execution_request_report(
            host_activation_plan_report=_host_activation_plan_report(),
            host_activation_plan_report_path="/tmp/data-ops-execution-request/host-plan.json",
            request_note="request explicit execution approval",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["execution_request"], "pending_explicit_execution_approval")
        self.assertTrue(report["requires_explicit_execution_approval"])
        self.assertTrue(report["execution_allowed_by_plan"])
        self.assertFalse(report["host_activation_execution_allowed_in_this_task"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertFalse(report["child_command_executed"])
        self.assertEqual(
            report["manual_next_step"],
            "data-operations-live-scheduler-host-activation-execution-decision",
        )
        self.assertIn("approve_host_activation_execution", report["requested_user_decision_values"])
        self.assertIn("deny_host_activation_execution", report["requested_user_decision_values"])
        self.assertIn("launchctl bootstrap", "\n".join(report["execution_command_preview"]))

    def test_rejects_non_ready_host_plan(self) -> None:
        plan = _host_activation_plan_report()
        plan["host_activation_plan"] = "blocked"
        plan["activation_allowed_for_execution_request"] = False

        with self.assertRaisesRegex(ValueError, "ready_for_execution_request"):
            build_data_operations_live_scheduler_host_activation_execution_request_report(
                host_activation_plan_report=plan,
            )

    def test_rejects_executed_step(self) -> None:
        plan = _host_activation_plan_report()
        plan["execution_plan_steps"] = [
            {
                "order": 1,
                "command_preview": "launchctl bootstrap gui/501 path.plist",
                "execution_status": "executed",
            }
        ]

        with self.assertRaisesRegex(ValueError, "must not have been executed"):
            build_data_operations_live_scheduler_host_activation_execution_request_report(
                host_activation_plan_report=plan,
            )

    def test_rejects_missing_command_preview(self) -> None:
        plan = _host_activation_plan_report()
        plan["rollback_plan_steps"] = []

        with self.assertRaisesRegex(ValueError, "command previews"):
            build_data_operations_live_scheduler_host_activation_execution_request_report(
                host_activation_plan_report=plan,
            )

    def test_rejects_secret_like_request_note(self) -> None:
        with self.assertRaisesRegex(ValueError, "secret-like"):
            build_data_operations_live_scheduler_host_activation_execution_request_report(
                host_activation_plan_report=_host_activation_plan_report(),
                request_note="postgresql://user:pass@host/db",
            )


def _host_activation_plan_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_host_activation_plan",
        "host_activation_plan": "ready_for_execution_request",
        "activation_allowed_for_execution_request": True,
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
        "final_preflight_report_path": "/tmp/data-ops-execution-request/final-preflight.json",
        "activation_request_report_path": "/tmp/data-ops-execution-request/live-activation-request.json",
        "execution_plan_steps": [
            {
                "order": 1,
                "command_preview": 'install -m 600 "/tmp/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
                "execution_status": "not_executed",
            },
            {
                "order": 2,
                "command_preview": 'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
                "execution_status": "not_executed",
            },
        ],
        "rollback_plan_steps": [
            {
                "order": 1,
                "command_preview": 'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
                "execution_status": "not_executed",
            },
            {
                "order": 2,
                "command_preview": 'rm -f "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
                "execution_status": "not_executed",
            },
        ],
        "manual_next_step": "data-operations-live-scheduler-host-activation-execution-request",
    }


if __name__ == "__main__":
    unittest.main()
