from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone

from stockanalysis.operations.scheduler_boundary import (
    build_data_operations_scheduler_preflight_report,
    build_data_operations_scheduler_skip_report,
)


class DataOperationsSchedulerBoundaryTests(unittest.TestCase):
    def test_preflight_report_redacts_command_and_marks_skip(self) -> None:
        report = build_data_operations_scheduler_preflight_report(
            job_id="macro-weekly",
            readiness_report={
                "runtime_env_readiness": "passed",
                "validated_env_groups": ["database", "fred", "artifact_root"],
            },
            command_argv=[
                "python3",
                "-m",
                "stockanalysis.ingest.cli",
                "macro-batch-upsert",
                "--api-key",
                "secret-value",
            ],
            run_date="2026-05-04",
            skip_dates="2026-05-04,2026-12-25",
            skip_reason="market_holiday",
            timeout_seconds=120,
        )

        self.assertEqual(report["report_name"], "data_operations_scheduler_preflight")
        self.assertEqual(report["preflight"], "passed")
        self.assertEqual(report["job_id"], "macro-weekly")
        self.assertEqual(report["pipeline_name"], "macro_upsert")
        self.assertTrue(report["would_skip"])
        self.assertIn("[REDACTED]", report["command_argv"])
        self.assertNotIn("secret-value", json.dumps(report))
        self.assertEqual(report["scheduler_activation"], "boundary_only_not_installed")

    def test_preflight_requires_passed_readiness(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_scheduler_preflight_report(
                job_id="macro-weekly",
                readiness_report={"runtime_env_readiness": "failed"},
                command_argv=["python3", "-c", "print('{}')"],
                run_date="2026-05-04",
            )

    def test_preflight_rejects_empty_command_and_unknown_job(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_scheduler_preflight_report(
                job_id="macro-weekly",
                readiness_report={"runtime_env_readiness": "passed"},
                command_argv=[],
                run_date="2026-05-04",
            )

        with self.assertRaises(ValueError):
            build_data_operations_scheduler_preflight_report(
                job_id="missing-job",
                readiness_report={"runtime_env_readiness": "passed"},
                command_argv=["python3"],
                run_date="2026-05-04",
            )

    def test_skip_report_requires_skip_date_hit(self) -> None:
        report = build_data_operations_scheduler_skip_report(
            job_id="macro-weekly",
            run_date="2026-05-04",
            skip_dates=["2026-05-04"],
            skip_reason="market_holiday",
            generated_at=datetime(2026, 5, 4, tzinfo=timezone.utc),
        )

        self.assertEqual(report["report_name"], "data_operations_scheduler_skip")
        self.assertEqual(report["status"], "skipped")
        self.assertEqual(report["generated_at"], "2026-05-04T00:00:00Z")

        with self.assertRaises(ValueError):
            build_data_operations_scheduler_skip_report(
                job_id="macro-weekly",
                run_date="2026-05-04",
                skip_dates=["2026-12-25"],
            )

    def test_invalid_dates_fail(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_scheduler_preflight_report(
                job_id="macro-weekly",
                readiness_report={"runtime_env_readiness": "passed"},
                command_argv=["python3"],
                run_date="20260504",
            )


if __name__ == "__main__":
    unittest.main()
