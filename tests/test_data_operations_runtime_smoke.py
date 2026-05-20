from __future__ import annotations

import json
import unittest

from stockanalysis.operations.runtime_smoke import build_data_operations_runtime_smoke_report


class DataOperationsRuntimeSmokeTests(unittest.TestCase):
    def test_smoke_report_combines_readiness_and_artifact_run_without_secrets(self) -> None:
        readiness = {
            "runtime_env_readiness": "passed",
            "validated_env_groups": ["database", "fred", "artifact_root"],
            "cadence_required_env_groups": ["database", "fred"],
        }
        artifact_run = {
            "job_id": "macro-weekly",
            "pipeline_name": "macro_upsert",
            "domain": "macro",
            "cadence": "weekly",
            "status": "succeeded",
            "exit_code": 0,
            "artifact_dir": "/tmp/artifacts/20260504T000000Z_macro-weekly",
            "metadata_path": "/tmp/artifacts/metadata.json",
            "stdout_path": "/tmp/artifacts/stdout.txt",
            "stdout_json_path": "/tmp/artifacts/stdout.json",
            "stderr_path": "/tmp/artifacts/stderr.log",
            "stdout_format": "json",
            "duration_ms": 12,
        }

        report = build_data_operations_runtime_smoke_report(
            readiness_report=readiness,
            artifact_run=artifact_run,
        )

        self.assertEqual(report["report_name"], "data_operations_runtime_smoke")
        self.assertEqual(report["runtime_smoke"], "passed")
        self.assertEqual(report["job_id"], "macro-weekly")
        self.assertEqual(report["scheduler_activation"], "not_activated")
        self.assertNotIn("postgresql://", json.dumps(report))

    def test_smoke_report_requires_passed_readiness(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_runtime_smoke_report(
                readiness_report={"runtime_env_readiness": "failed"},
                artifact_run={"status": "succeeded", "exit_code": 0},
            )

    def test_smoke_report_fails_failed_artifact_run(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_runtime_smoke_report(
                readiness_report={"runtime_env_readiness": "passed"},
                artifact_run={"job_id": "macro-weekly", "status": "failed", "exit_code": 7},
            )

    def test_smoke_report_rejects_secret_like_values(self) -> None:
        with self.assertRaises(ValueError):
            build_data_operations_runtime_smoke_report(
                readiness_report={"runtime_env_readiness": "passed"},
                artifact_run={
                    "job_id": "macro-weekly",
                    "status": "succeeded",
                    "exit_code": 0,
                    "artifact_dir": "postgresql://runtime_user:runtime_pass@db",
                },
            )


if __name__ == "__main__":
    unittest.main()
