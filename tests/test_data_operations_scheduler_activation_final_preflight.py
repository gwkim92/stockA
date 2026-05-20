from __future__ import annotations

from datetime import datetime, timezone
import unittest

from stockanalysis.operations.scheduler_activation_final_preflight import (
    build_data_operations_live_scheduler_activation_final_preflight_report,
)


class DataOperationsSchedulerActivationFinalPreflightTests(unittest.TestCase):
    def test_passes_for_approved_decision_and_fresh_runtime_readiness(self) -> None:
        report = build_data_operations_live_scheduler_activation_final_preflight_report(
            activation_decision_report=_decision_report(),
            activation_request_report=_request_report(),
            approval_gate_report=_approval_gate_report(),
            operator_dry_run_report=_operator_dry_run_report(),
            runtime_env_readiness_report=_runtime_readiness_report("passed"),
            activation_decision_report_path="/tmp/data-ops-final/decision.json",
            activation_request_report_path="/tmp/data-ops-final/request.json",
            approval_gate_report_path="/tmp/data-ops-final/gate.json",
            operator_dry_run_report_path="/tmp/data-ops-final/operator.json",
            runtime_env_readiness_report_path="/tmp/data-ops-final/runtime.json",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["final_preflight"], "passed_ready_for_host_activation_plan")
        self.assertTrue(report["activation_allowed_for_host_activation_plan"])
        self.assertFalse(report["host_activation_execution_allowed_in_this_task"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-host-activation-plan")

    def test_blocks_denied_user_decision(self) -> None:
        decision = _decision_report()
        decision["decision_gate"] = "denied_live_scheduler_activation"
        decision["user_decision"] = "deny_live_scheduler_activation"
        decision["activation_allowed_for_next_task"] = False
        decision["manual_next_step"] = "data-operations-live-scheduler-activation-request"

        report = build_data_operations_live_scheduler_activation_final_preflight_report(
            activation_decision_report=decision,
            activation_request_report=_request_report(),
            approval_gate_report=_approval_gate_report(),
            operator_dry_run_report=_operator_dry_run_report(),
            runtime_env_readiness_report=_runtime_readiness_report("passed"),
        )

        self.assertEqual(report["final_preflight"], "blocked_user_decision_not_approved")
        self.assertFalse(report["activation_allowed_for_host_activation_plan"])
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-activation-user-decision")

    def test_blocks_failed_runtime_readiness(self) -> None:
        report = build_data_operations_live_scheduler_activation_final_preflight_report(
            activation_decision_report=_decision_report(),
            activation_request_report=_request_report(),
            approval_gate_report=_approval_gate_report(),
            operator_dry_run_report=_operator_dry_run_report(),
            runtime_env_readiness_report=_runtime_readiness_report("failed"),
        )

        self.assertEqual(report["final_preflight"], "blocked_runtime_env_not_ready")
        self.assertFalse(report["activation_allowed_for_host_activation_plan"])
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-activation-final-preflight")

    def test_rejects_mismatched_referenced_paths(self) -> None:
        with self.assertRaisesRegex(ValueError, "approval gate report path"):
            build_data_operations_live_scheduler_activation_final_preflight_report(
                activation_decision_report=_decision_report(),
                activation_request_report=_request_report(),
                approval_gate_report=_approval_gate_report(),
                operator_dry_run_report=_operator_dry_run_report(),
                runtime_env_readiness_report=_runtime_readiness_report("passed"),
                approval_gate_report_path="/tmp/data-ops-final/wrong-gate.json",
            )

    def test_rejects_secret_like_runtime_readiness_payload(self) -> None:
        runtime = _runtime_readiness_report("passed")
        runtime["issues"] = ["DATABASE_URL=postgresql://user:pass@host/db"]

        with self.assertRaisesRegex(ValueError, "secret-like"):
            build_data_operations_live_scheduler_activation_final_preflight_report(
                activation_decision_report=_decision_report(),
                activation_request_report=_request_report(),
                approval_gate_report=_approval_gate_report(),
                operator_dry_run_report=_operator_dry_run_report(),
                runtime_env_readiness_report=runtime,
            )


def _decision_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_activation_user_decision",
        "decision_gate": "approved_for_live_scheduler_activation_final_preflight",
        "user_decision": "approve_live_scheduler_activation",
        "activation_allowed_for_next_task": True,
        "activation_execution_allowed_in_this_task": False,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "job_id": "macro-weekly",
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "activation_request_report_path": "/tmp/data-ops-final/request.json",
        "manual_next_step": "data-operations-live-scheduler-activation-final-preflight",
    }


def _request_report() -> dict[str, object]:
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
        "approval_gate_report_path": "/tmp/data-ops-final/gate.json",
        "operator_dry_run_report_path": "/tmp/data-ops-final/operator.json",
        "manual_next_step": "data-operations-live-scheduler-activation-user-decision",
    }


def _approval_gate_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_scheduler_activation_approval_gate",
        "approval_gate": "approved_for_manual_activation",
        "activation_allowed": True,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "job_id": "macro-weekly",
    }


def _operator_dry_run_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_scheduler_operator_dry_run",
        "operator_dry_run": "passed",
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "requires_manual_approval": True,
        "job_id": "macro-weekly",
    }


def _runtime_readiness_report(status: str) -> dict[str, object]:
    return {
        "report_name": "data_operations_runtime_env_readiness",
        "runtime_env_readiness": status,
        "env_file": "/tmp/data-ops-final/data-operations.env",
        "issues": [] if status == "passed" else ["missing env"],
        "secrets_policy": "values_redacted_env_names_only",
    }


if __name__ == "__main__":
    unittest.main()
