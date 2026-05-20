from __future__ import annotations

from datetime import datetime, timezone
import unittest

from stockanalysis.operations.scheduler_activation_request import (
    build_data_operations_live_scheduler_activation_request_report,
)


class DataOperationsSchedulerActivationRequestTests(unittest.TestCase):
    def test_builds_pending_user_activation_request(self) -> None:
        report = build_data_operations_live_scheduler_activation_request_report(
            approval_gate_report=_approved_gate_report(),
            operator_dry_run_report=_operator_dry_run_report(),
            approval_gate_report_path="/tmp/stockanalysis/approved-gate.json",
            operator_dry_run_report_path="/tmp/stockanalysis/operator-dry-run.json",
            request_note="request explicit user decision",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["report_name"], "data_operations_live_scheduler_activation_request")
        self.assertEqual(report["activation_request"], "pending_explicit_user_approval")
        self.assertTrue(report["requires_explicit_user_approval"])
        self.assertTrue(report["activation_allowed_by_gate"])
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertFalse(report["child_command_executed"])
        self.assertEqual(report["job_id"], "macro-weekly")
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-activation-user-decision")
        self.assertIn("approve_live_scheduler_activation", report["requested_user_decision_values"])
        self.assertIn("deny_live_scheduler_activation", report["requested_user_decision_values"])
        self.assertIn("launchctl bootstrap", "\n".join(report["activation_command_preview"]))
        self.assertEqual(
            report["host_plist_path_preview"],
            "$HOME/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist",
        )
        command_text = "\n".join(report["activation_command_preview"] + report["rollback_command_preview"])
        self.assertIn('"$HOME/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"', command_text)
        self.assertNotIn('"~/Library/LaunchAgents', command_text)

    def test_rejects_pending_gate_report(self) -> None:
        gate = _approved_gate_report()
        gate["approval_gate"] = "blocked_pending_manual_approval"
        gate["activation_allowed"] = False

        with self.assertRaisesRegex(ValueError, "approved_for_manual_activation"):
            build_data_operations_live_scheduler_activation_request_report(
                approval_gate_report=gate,
                operator_dry_run_report=_operator_dry_run_report(),
            )

    def test_rejects_mismatched_operator_report(self) -> None:
        operator_report = _operator_dry_run_report()
        operator_report["job_id"] = "other-job"

        with self.assertRaisesRegex(ValueError, "job_id"):
            build_data_operations_live_scheduler_activation_request_report(
                approval_gate_report=_approved_gate_report(),
                operator_dry_run_report=operator_report,
            )

    def test_rejects_path_mismatch_against_gate_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "path"):
            build_data_operations_live_scheduler_activation_request_report(
                approval_gate_report=_approved_gate_report(),
                operator_dry_run_report=_operator_dry_run_report(),
                operator_dry_run_report_path="/tmp/stockanalysis/wrong-report.json",
            )

    def test_rejects_secret_like_request_note(self) -> None:
        with self.assertRaisesRegex(ValueError, "secret-like"):
            build_data_operations_live_scheduler_activation_request_report(
                approval_gate_report=_approved_gate_report(),
                operator_dry_run_report=_operator_dry_run_report(),
                request_note="DATABASE_URL=postgresql://user:pass@host/db",
            )


def _approved_gate_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_scheduler_activation_approval_gate",
        "approval_gate": "approved_for_manual_activation",
        "activation_allowed": True,
        "approval_decision": "approved",
        "operator": "operator-handle",
        "approved_at": "2026-05-11T12:00:00Z",
        "activation_window": "2026-05-11T12:00:00Z/2026-05-11T13:00:00Z",
        "rollback_owner": "operator-handle",
        "acknowledged_commands": [
            "install -m 600",
            "launchctl bootstrap",
            "launchctl kickstart",
            "launchctl print",
        ],
        "acknowledged_risks": [
            "host_scheduler_state_change",
            "recurring_data_operation_execution",
            "rollback_required_if_first_run_fails",
        ],
        "job_id": "macro-weekly",
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "operator_dry_run": "passed",
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "operator_dry_run_report_path": "/tmp/stockanalysis/operator-dry-run.json",
        "approval_record_path": "/tmp/stockanalysis/activation-approval.json",
        "manual_next_step": "data-operations-live-scheduler-activation-request",
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
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "output_dir": "/tmp/stockanalysis/operator-dry-run",
        "evidence_paths": {
            "env_readiness_report": "/tmp/stockanalysis/evidence/env-readiness.json",
            "scheduler_preflight_report": "/tmp/stockanalysis/evidence/scheduler-preflight.json",
            "install_manifest": "/tmp/stockanalysis/rendered/manifest.json",
            "plist": "/tmp/stockanalysis/rendered/com.stockanalysis.data-operations.macro-weekly.plist",
            "alert_validation_output": "/tmp/stockanalysis/evidence/alert-rule-validation.txt",
        },
        "rendered_label": "com.stockanalysis.data-operations.macro-weekly",
        "rendered_scheduler_type": "launchd",
        "manual_next_step": "data-operations-scheduler-activation-approval-gate",
    }


if __name__ == "__main__":
    unittest.main()
