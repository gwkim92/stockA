from __future__ import annotations

from datetime import datetime, timezone
import unittest

from stockanalysis.operations.scheduler_activation_execution_final_preflight import (
    build_data_operations_live_scheduler_host_activation_execution_final_preflight_report,
)


class DataOperationsSchedulerActivationExecutionFinalPreflightTests(unittest.TestCase):
    def test_passes_for_approved_execution_decision_and_fresh_runtime_readiness(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_execution_final_preflight_report(
            execution_decision_report=_execution_decision_report(),
            execution_request_report=_execution_request_report(),
            host_activation_plan_report=_host_activation_plan_report(),
            runtime_env_readiness_report=_runtime_readiness_report("passed"),
            execution_decision_report_path="/tmp/data-ops-execution-final/decision.json",
            execution_request_report_path="/tmp/data-ops-execution-final/request.json",
            host_activation_plan_report_path="/tmp/data-ops-execution-final/host-plan.json",
            runtime_env_readiness_report_path="/tmp/data-ops-execution-final/runtime.json",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["execution_final_preflight"], "passed_ready_for_host_activation_execution_task")
        self.assertTrue(report["host_activation_execution_allowed_for_next_task"])
        self.assertFalse(report["host_activation_execution_allowed_in_this_task"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-host-activation-execution")
        self.assertIn("launchctl bootstrap", "\n".join(report["execution_command_preview"]))

    def test_blocks_denied_execution_decision(self) -> None:
        decision = _execution_decision_report()
        decision["decision_gate"] = "denied_host_activation_execution"
        decision["user_decision"] = "deny_host_activation_execution"
        decision["host_activation_execution_allowed_for_next_task"] = False
        decision["manual_next_step"] = "data-operations-live-scheduler-host-activation-execution-request"

        report = build_data_operations_live_scheduler_host_activation_execution_final_preflight_report(
            execution_decision_report=decision,
            execution_request_report=_execution_request_report(),
            host_activation_plan_report=_host_activation_plan_report(),
            runtime_env_readiness_report=_runtime_readiness_report("passed"),
        )

        self.assertEqual(report["execution_final_preflight"], "blocked_execution_decision_not_approved")
        self.assertFalse(report["host_activation_execution_allowed_for_next_task"])
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-host-activation-execution-decision")

    def test_blocks_failed_runtime_readiness(self) -> None:
        report = build_data_operations_live_scheduler_host_activation_execution_final_preflight_report(
            execution_decision_report=_execution_decision_report(),
            execution_request_report=_execution_request_report(),
            host_activation_plan_report=_host_activation_plan_report(),
            runtime_env_readiness_report=_runtime_readiness_report("failed"),
        )

        self.assertEqual(report["execution_final_preflight"], "blocked_runtime_env_not_ready")
        self.assertFalse(report["host_activation_execution_allowed_for_next_task"])
        self.assertEqual(
            report["manual_next_step"],
            "data-operations-live-scheduler-host-activation-execution-final-preflight",
        )

    def test_rejects_mismatched_host_plan_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "host activation plan report path"):
            build_data_operations_live_scheduler_host_activation_execution_final_preflight_report(
                execution_decision_report=_execution_decision_report(),
                execution_request_report=_execution_request_report(),
                host_activation_plan_report=_host_activation_plan_report(),
                runtime_env_readiness_report=_runtime_readiness_report("passed"),
                host_activation_plan_report_path="/tmp/data-ops-execution-final/wrong-host-plan.json",
            )

    def test_rejects_command_preview_drift(self) -> None:
        request = _execution_request_report()
        request["execution_command_preview"] = ["launchctl bootstrap different.plist"]

        with self.assertRaisesRegex(ValueError, "command preview must match"):
            build_data_operations_live_scheduler_host_activation_execution_final_preflight_report(
                execution_decision_report=_execution_decision_report(),
                execution_request_report=request,
                host_activation_plan_report=_host_activation_plan_report(),
                runtime_env_readiness_report=_runtime_readiness_report("passed"),
            )

    def test_rejects_secret_like_runtime_readiness_payload(self) -> None:
        runtime = _runtime_readiness_report("passed")
        runtime["issues"] = ["DATABASE_URL=postgresql://user:pass@host/db"]

        with self.assertRaisesRegex(ValueError, "secret-like"):
            build_data_operations_live_scheduler_host_activation_execution_final_preflight_report(
                execution_decision_report=_execution_decision_report(),
                execution_request_report=_execution_request_report(),
                host_activation_plan_report=_host_activation_plan_report(),
                runtime_env_readiness_report=runtime,
            )


def _execution_decision_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_host_activation_execution_decision",
        "decision_gate": "approved_for_host_activation_execution_final_preflight",
        "user_decision": "approve_host_activation_execution",
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
        "execution_request_report_path": "/tmp/data-ops-execution-final/request.json",
        "manual_next_step": "data-operations-live-scheduler-host-activation-execution-final-preflight",
    }


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
        "rendered_label": "com.stockanalysis.data-operations.macro-weekly",
        "host_plist_path_preview": "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist",
        "host_activation_plan_report_path": "/tmp/data-ops-execution-final/host-plan.json",
        "execution_command_preview": [
            'install -m 600 "/tmp/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
        "rollback_command_preview": [
            'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
        "manual_next_step": "data-operations-live-scheduler-host-activation-execution-decision",
    }


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
            }
        ],
        "manual_next_step": "data-operations-live-scheduler-host-activation-execution-request",
    }


def _runtime_readiness_report(status: str) -> dict[str, object]:
    return {
        "report_name": "data_operations_runtime_env_readiness",
        "runtime_env_readiness": status,
        "env_file": "/tmp/data-ops-execution-final/data-operations.env",
        "issues": [] if status == "passed" else ["missing env"],
        "secrets_policy": "values_redacted_env_names_only",
    }


if __name__ == "__main__":
    unittest.main()
