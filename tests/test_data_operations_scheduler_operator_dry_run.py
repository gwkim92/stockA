from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone

from stockanalysis.operations.scheduler_operator_dry_run import (
    build_data_operations_scheduler_operator_dry_run_report,
)


class DataOperationsSchedulerOperatorDryRunTests(unittest.TestCase):
    def test_report_combines_readiness_preflight_install_and_alert_evidence(self) -> None:
        report = build_data_operations_scheduler_operator_dry_run_report(
            job_id="macro-weekly",
            output_dir="/tmp/operator-dry-run",
            readiness_report={
                "runtime_env_readiness": "passed",
                "validated_env_groups": ["database", "artifact_root"],
            },
            preflight_report={
                "preflight": "passed",
                "scheduler_activation": "boundary_only_not_installed",
                "job_id": "macro-weekly",
                "pipeline_name": "macro_upsert",
                "domain": "macro",
                "cadence": "weekly",
            },
            install_manifest={
                "install_mode": "dry_run",
                "scheduler_activation": "not_installed",
                "host_install_path_written": False,
                "job_id": "macro-weekly",
                "label": "com.stockanalysis.data-operations.macro-weekly",
                "scheduler_type": "launchd",
            },
            alert_validation_output="validated ops/observability/data-operations-alert-rules.yml with 6 alert rules",
            evidence_paths={
                "env_readiness_report": "/tmp/operator-dry-run/env-readiness.json",
                "scheduler_preflight_report": "/tmp/operator-dry-run/scheduler-preflight.json",
                "install_manifest": "/tmp/operator-dry-run/rendered/manifest.json",
                "plist": "/tmp/operator-dry-run/rendered/job.plist",
                "alert_validation_output": "/tmp/operator-dry-run/alert-rule-validation.txt",
            },
            generated_at=datetime(2026, 5, 11, tzinfo=timezone.utc),
        )

        self.assertEqual(report["report_name"], "data_operations_scheduler_operator_dry_run")
        self.assertEqual(report["operator_dry_run"], "passed")
        self.assertEqual(report["scheduler_activation"], "not_installed")
        self.assertFalse(report["launchctl_executed"])
        self.assertFalse(report["child_command_executed"])
        self.assertTrue(report["requires_manual_approval"])
        self.assertEqual(report["manual_next_step"], "data-operations-scheduler-activation-approval-gate")
        self.assertNotIn("postgresql://", json.dumps(report))

    def test_report_rejects_failed_readiness_or_host_install_write(self) -> None:
        base = {
            "job_id": "macro-weekly",
            "output_dir": "/tmp/operator-dry-run",
            "readiness_report": {"runtime_env_readiness": "passed"},
            "preflight_report": {
                "preflight": "passed",
                "scheduler_activation": "boundary_only_not_installed",
                "job_id": "macro-weekly",
            },
            "install_manifest": {
                "install_mode": "dry_run",
                "scheduler_activation": "not_installed",
                "host_install_path_written": False,
                "job_id": "macro-weekly",
            },
            "alert_validation_output": "validated rules",
            "evidence_paths": {
                "env_readiness_report": "/tmp/env.json",
                "scheduler_preflight_report": "/tmp/preflight.json",
                "install_manifest": "/tmp/manifest.json",
                "plist": "/tmp/job.plist",
                "alert_validation_output": "/tmp/alerts.txt",
            },
        }

        with self.assertRaises(ValueError):
            build_data_operations_scheduler_operator_dry_run_report(
                **{**base, "readiness_report": {"runtime_env_readiness": "failed"}}
            )

        with self.assertRaises(ValueError):
            build_data_operations_scheduler_operator_dry_run_report(
                **{
                    **base,
                    "install_manifest": {
                        "install_mode": "dry_run",
                        "scheduler_activation": "not_installed",
                        "host_install_path_written": True,
                        "job_id": "macro-weekly",
                    },
                }
            )

    def test_report_requires_complete_evidence_paths(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_scheduler_operator_dry_run_report(
                job_id="macro-weekly",
                output_dir="/tmp/operator-dry-run",
                readiness_report={"runtime_env_readiness": "passed"},
                preflight_report={
                    "preflight": "passed",
                    "scheduler_activation": "boundary_only_not_installed",
                    "job_id": "macro-weekly",
                },
                install_manifest={
                    "install_mode": "dry_run",
                    "scheduler_activation": "not_installed",
                    "host_install_path_written": False,
                    "job_id": "macro-weekly",
                },
                alert_validation_output="validated rules",
                evidence_paths={},
            )


if __name__ == "__main__":
    unittest.main()
