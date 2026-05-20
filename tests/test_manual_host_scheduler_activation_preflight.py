from __future__ import annotations

from datetime import datetime, timezone
import unittest

from stockanalysis.operations.manual_host_scheduler_activation_preflight import (
    build_manual_host_scheduler_activation_preflight_report,
)


class ManualHostSchedulerActivationPreflightTests(unittest.TestCase):
    def test_passes_for_approved_manual_packet_and_runtime_ready(self) -> None:
        report = build_manual_host_scheduler_activation_preflight_report(
            manual_approval_report=_manual_approval_report(),
            runtime_env_readiness_report=_runtime_readiness("passed"),
            manual_approval_report_path="/tmp/manual-approval.json",
            runtime_env_readiness_report_path="/tmp/runtime-readiness.json",
            generated_at=datetime(2026, 5, 15, tzinfo=timezone.utc),
        )

        self.assertEqual(
            report["manual_activation_preflight"],
            "passed_ready_for_external_manual_host_scheduler_activation",
        )
        self.assertTrue(report["manual_operator_may_execute_exact_commands"])
        self.assertFalse(report["codex_host_mutation_allowed"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertEqual(report["manual_next_step"], "manual-host-scheduler-activation-operator-evidence")

    def test_blocks_when_manual_approval_is_not_ready(self) -> None:
        approval = _manual_approval_report()
        approval["approval_gate"] = "blocked_pending_exact_host_command_approval"
        approval["host_activation_allowed_for_manual_operator"] = False

        report = build_manual_host_scheduler_activation_preflight_report(
            manual_approval_report=approval,
            runtime_env_readiness_report=_runtime_readiness("passed"),
        )

        self.assertEqual(report["manual_activation_preflight"], "blocked_manual_approval_not_ready")
        self.assertFalse(report["manual_operator_may_execute_exact_commands"])
        self.assertEqual(report["manual_next_step"], "manual-host-scheduler-activation-explicit-approval")

    def test_blocks_when_runtime_env_is_not_ready(self) -> None:
        report = build_manual_host_scheduler_activation_preflight_report(
            manual_approval_report=_manual_approval_report(),
            runtime_env_readiness_report=_runtime_readiness("failed"),
        )

        self.assertEqual(report["manual_activation_preflight"], "blocked_runtime_env_not_ready")
        self.assertFalse(report["manual_operator_may_execute_exact_commands"])
        self.assertIn("missing", report["runtime_env_issues"])

    def test_rejects_approval_report_that_claims_launchctl_was_executed(self) -> None:
        approval = _manual_approval_report()
        approval["launchctl_executed"] = True

        with self.assertRaisesRegex(ValueError, "must not execute launchctl"):
            build_manual_host_scheduler_activation_preflight_report(
                manual_approval_report=approval,
                runtime_env_readiness_report=_runtime_readiness("passed"),
            )

    def test_rejects_secret_like_runtime_readiness_payload(self) -> None:
        readiness = _runtime_readiness("failed")
        readiness["issues"] = ["postgresql://user:pass@host/db"]

        with self.assertRaisesRegex(ValueError, "secret-like"):
            build_manual_host_scheduler_activation_preflight_report(
                manual_approval_report=_manual_approval_report(),
                runtime_env_readiness_report=readiness,
            )


def _manual_approval_report() -> dict[str, object]:
    return {
        "report_name": "manual_host_scheduler_activation_explicit_approval",
        "approval_gate": "approved_for_manual_operator_host_activation_not_executed_by_codex",
        "host_activation_allowed_for_manual_operator": True,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_performed": False,
        "codex_host_mutation_allowed": False,
        "job_id": "macro-weekly",
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "rendered_label": "com.stockanalysis.data-operations.macro-weekly",
        "host_plist_path_preview": "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist",
        "exact_execution_commands": _execution_commands(),
        "exact_rollback_commands": _rollback_commands(),
        "manual_next_step": "manual-host-scheduler-activation-operator-evidence",
    }


def _runtime_readiness(status: str) -> dict[str, object]:
    return {
        "report_name": "data_operations_runtime_env_readiness",
        "runtime_env_readiness": status,
        "issues": [] if status == "passed" else ["missing"],
        "secrets_policy": "values_redacted_env_names_only",
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
