from __future__ import annotations

import json
import unittest
from pathlib import Path

from stockanalysis.operations.scheduler_install import (
    build_data_operations_launchd_plist,
    build_data_operations_scheduler_install_manifest,
    default_launchd_label,
)


class DataOperationsSchedulerInstallTests(unittest.TestCase):
    def test_launchd_plist_for_weekly_job_calls_scheduler_wrapper(self) -> None:
        plist = build_data_operations_launchd_plist(
            job_id="macro-weekly",
            repo_root="/repo",
            env_file="/secure/data-operations.env",
            wrapper_path="/repo/scripts/run_data_operations_scheduler_job.sh",
            output_dir="/tmp/rendered",
            command_argv=["python3", "-m", "stockanalysis.ingest.cli", "macro-batch-upsert"],
            timeout_seconds=120,
        )

        self.assertEqual(plist["Label"], "com.stockanalysis.data-operations.macro-weekly")
        self.assertEqual(plist["ProgramArguments"][0], "/bin/bash")
        self.assertEqual(plist["WorkingDirectory"], "/repo")
        command = plist["ProgramArguments"][2]
        self.assertIn("run_data_operations_scheduler_job.sh", command)
        self.assertIn("--env-file /secure/data-operations.env", command)
        self.assertIn("--job-id macro-weekly", command)
        self.assertIn("--timeout-seconds 120", command)
        self.assertEqual(plist["StartCalendarInterval"], [{"Weekday": 2, "Hour": 7, "Minute": 30}])
        self.assertFalse(plist["RunAtLoad"])

    def test_launchd_plist_for_daily_job_uses_weekdays(self) -> None:
        plist = build_data_operations_launchd_plist(
            job_id="market-price-daily",
            repo_root="/repo",
            env_file="/secure/data-operations.env",
            wrapper_path="/repo/scripts/run_data_operations_scheduler_job.sh",
            output_dir="/tmp/rendered",
            command_argv=["python3", "-c", "print('{}')"],
        )

        schedule = plist["StartCalendarInterval"]
        self.assertEqual({item["Weekday"] for item in schedule}, {2, 3, 4, 5, 6})
        self.assertEqual({item["Hour"] for item in schedule}, {18})
        self.assertEqual({item["Minute"] for item in schedule}, {30})

    def test_monthly_first_business_day_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_launchd_plist(
                job_id="performance-outcome-monthly",
                repo_root="/repo",
                env_file="/secure/data-operations.env",
                wrapper_path="/repo/scripts/run_data_operations_scheduler_job.sh",
                output_dir="/tmp/rendered",
                command_argv=["python3"],
            )

    def test_install_manifest_is_secret_free_metadata(self) -> None:
        manifest = build_data_operations_scheduler_install_manifest(
            job_id="macro-weekly",
            label=default_launchd_label("macro-weekly"),
            plist_path="/tmp/rendered/com.stockanalysis.data-operations.macro-weekly.plist",
            env_file="/secure/data-operations.env",
            wrapper_path="/repo/scripts/run_data_operations_scheduler_job.sh",
            output_dir="/tmp/rendered",
            command_argv=["python3", "-m", "stockanalysis.ingest.cli", "macro-batch-upsert"],
            timeout_seconds=120,
        )

        self.assertEqual(manifest["report_name"], "data_operations_scheduler_install_dry_run")
        self.assertEqual(manifest["install_mode"], "dry_run")
        self.assertEqual(manifest["scheduler_activation"], "not_installed")
        self.assertFalse(manifest["host_install_path_written"])
        self.assertNotIn("postgresql://", json.dumps(manifest))

    def test_sensitive_command_args_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_launchd_plist(
                job_id="macro-weekly",
                repo_root="/repo",
                env_file="/secure/data-operations.env",
                wrapper_path="/repo/scripts/run_data_operations_scheduler_job.sh",
                output_dir="/tmp/rendered",
                command_argv=["python3", "-c", "print('{}')", "--api-key", "secret-value"],
            )

    def test_default_label_rejects_empty_safe_job_id(self) -> None:
        with self.assertRaises(ValueError):
            default_launchd_label("!!!")


if __name__ == "__main__":
    unittest.main()
