from __future__ import annotations

import unittest
from datetime import datetime, timezone

from stockanalysis.operations.scheduler_activation_approval import (
    build_data_operations_scheduler_activation_approval_gate_report,
)


class DataOperationsSchedulerActivationApprovalTests(unittest.TestCase):
    def test_missing_approval_record_blocks_activation(self) -> None:
        report = build_data_operations_scheduler_activation_approval_gate_report(
            operator_dry_run_report=_operator_dry_run_report(),
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["approval_gate"], "blocked_pending_manual_approval")
        self.assertFalse(report["activation_allowed"])
        self.assertFalse(report["launchctl_executed"])
        self.assertEqual(report["manual_next_step"], "data-operations-live-scheduler-activation-request")

    def test_approved_record_allows_manual_activation_without_executing_it(self) -> None:
        approval = _approval_record()
        report = build_data_operations_scheduler_activation_approval_gate_report(
            operator_dry_run_report=_operator_dry_run_report(),
            approval_record=approval,
            approval_record_path="/tmp/approval.json",
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["approval_gate"], "approved_for_manual_activation")
        self.assertTrue(report["activation_allowed"])
        self.assertEqual(report["approval_decision"], "approved")
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["host_install_path_written"])
        self.assertEqual(report["operator"], "operator-handle")

    def test_approval_record_must_match_job_and_acknowledge_risks(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_scheduler_activation_approval_gate_report(
                operator_dry_run_report=_operator_dry_run_report(),
                approval_record={**_approval_record(), "job_id": "market-price-daily"},
            )

        with self.assertRaises(ValueError):
            build_data_operations_scheduler_activation_approval_gate_report(
                operator_dry_run_report=_operator_dry_run_report(),
                approval_record={**_approval_record(), "acknowledged_risks": []},
            )

    def test_secret_like_values_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_scheduler_activation_approval_gate_report(
                operator_dry_run_report=_operator_dry_run_report(),
                approval_record={
                    **_approval_record(),
                    "operator": "postgresql://user:password@db.internal/stockanalysis",
                },
            )


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
        "pipeline_name": "macro_upsert",
        "domain": "macro",
        "cadence": "weekly",
        "evidence_paths": {
            "operator_dry_run_report": "/tmp/operator-dry-run/evidence/operator-dry-run.json"
        },
    }


def _approval_record() -> dict[str, object]:
    return {
        "approval_record": "data_operations_scheduler_activation_approval",
        "approval_decision": "approved",
        "operator": "operator-handle",
        "approved_at": "2026-05-11T12:00:00Z",
        "job_id": "macro-weekly",
        "operator_dry_run_report": "/tmp/operator-dry-run/evidence/operator-dry-run.json",
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
    }


if __name__ == "__main__":
    unittest.main()
