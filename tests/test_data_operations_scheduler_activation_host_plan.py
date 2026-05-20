from __future__ import annotations

from datetime import datetime, timezone
import unittest

from stockanalysis.operations.scheduler_activation_host_plan import (
    build_data_operations_live_scheduler_host_activation_plan_report,
    render_data_operations_live_scheduler_host_activation_plan_markdown,
)


class DataOperationsSchedulerActivationHostPlanTests(unittest.TestCase):
    def test_builds_host_activation_plan_without_execution(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_plan_report(
            final_preflight_report=_final_preflight_report(),
            activation_request_report=_activation_request_report(),
            final_preflight_report_path="/tmp/data-ops-host-plan/final-preflight.json",
            activation_request_report_path="/tmp/data-ops-host-plan/request.json",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["host_activation_plan"], "ready_for_execution_request")
        self.assertTrue(report["activation_allowed_for_execution_request"])
        self.assertFalse(report["host_activation_execution_allowed_in_this_task"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-host-activation-execution-request")
        self.assertIn("launchctl bootstrap", json_preview(report["execution_plan_steps"]))

    def test_render_markdown_plan(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_plan_report(
            final_preflight_report=_final_preflight_report(),
            activation_request_report=_activation_request_report(),
            final_preflight_report_path="/tmp/data-ops-host-plan/final-preflight.json",
            activation_request_report_path="/tmp/data-ops-host-plan/request.json",
        )

        markdown = render_data_operations_live_scheduler_host_activation_plan_markdown(report)

        self.assertIn("Data Operations Host Activation Plan", markdown)
        self.assertIn("launchctl bootstrap", markdown)
        self.assertIn("data-operations-live-scheduler-host-activation-execution-request", markdown)

    def test_rejects_non_passing_final_preflight(self) -> None:
        final = _final_preflight_report()
        final["final_preflight"] = "blocked_runtime_env_not_ready"
        final["activation_allowed_for_host_activation_plan"] = False

        with self.assertRaisesRegex(ValueError, "passed_ready_for_host_activation_plan"):
            build_data_operations_live_scheduler_host_activation_plan_report(
                final_preflight_report=final,
                activation_request_report=_activation_request_report(),
            )

    def test_rejects_path_mismatch(self) -> None:
        with self.assertRaisesRegex(ValueError, "activation request report path"):
            build_data_operations_live_scheduler_host_activation_plan_report(
                final_preflight_report=_final_preflight_report(),
                activation_request_report=_activation_request_report(),
                activation_request_report_path="/tmp/data-ops-host-plan/wrong-request.json",
            )

    def test_rejects_secret_like_command_preview(self) -> None:
        request = _activation_request_report()
        request["activation_command_preview"] = ["launchctl bootstrap postgresql://user:pass@host/db"]

        with self.assertRaisesRegex(ValueError, "secret-like"):
            build_data_operations_live_scheduler_host_activation_plan_report(
                final_preflight_report=_final_preflight_report(),
                activation_request_report=request,
            )


def json_preview(steps: object) -> str:
    return "\n".join(str(step) for step in steps)


def _final_preflight_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_activation_final_preflight",
        "final_preflight": "passed_ready_for_host_activation_plan",
        "activation_allowed_for_host_activation_plan": True,
        "host_activation_execution_allowed_in_this_task": False,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "job_id": "macro-weekly",
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "activation_request_report_path": "/tmp/data-ops-host-plan/request.json",
        "manual_next_step": "data-operations-live-scheduler-host-activation-plan",
    }


def _activation_request_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_activation_request",
        "activation_request": "pending_explicit_user_approval",
        "activation_allowed_by_gate": True,
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
        "activation_command_preview": [
            'install -m 600 "/tmp/data-ops-host-plan/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            'launchctl kickstart -k "gui/$(id -u)/com.stockanalysis.data-operations.macro-weekly"',
            'launchctl print "gui/$(id -u)/com.stockanalysis.data-operations.macro-weekly"',
        ],
        "rollback_command_preview": [
            'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            'rm -f "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
    }


if __name__ == "__main__":
    unittest.main()
