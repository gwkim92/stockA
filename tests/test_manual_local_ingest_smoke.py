from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stockanalysis.operations.manual_local_ingest_smoke import (
    build_manual_local_ingest_job,
    build_manual_local_ingest_smoke_report,
    load_manual_local_ingest_smoke_visibility_report,
)


class ManualLocalIngestSmokeTests(unittest.TestCase):
    def test_preview_does_not_call_runner_and_redacts_env_values(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = _write_runtime_env(Path(runtime_root))
            calls: list[object] = []

            report = build_manual_local_ingest_smoke_report(
                repo_root=repo_root,
                runtime_root=runtime_path,
                execute=False,
                python_executable="/usr/bin/python3",
                runner=lambda **kwargs: calls.append(kwargs) or {},
            )

            self.assertEqual(report["report_name"], "manual_local_ingest_smoke")
            self.assertEqual(report["smoke_status"], "preview_not_executed")
            self.assertFalse(report["execute"])
            self.assertEqual(report["job_count"], 3)
            self.assertEqual(calls, [])
            report_text = json.dumps(report)
            self.assertNotIn("hidden-db-password", report_text)
            self.assertNotIn("hidden-twelve-key", report_text)
            self.assertNotIn("postgresql://", report_text)
            self.assertIn("market-price-daily", report_text)
            self.assertIn("--execute", " ".join(report["next_actions"]))

    def test_execute_calls_artifact_runner_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = _write_runtime_env(Path(runtime_root))
            calls: list[dict[str, object]] = []

            def runner(**kwargs: object) -> dict[str, object]:
                calls.append(dict(kwargs))
                return {
                    "job_id": kwargs["job_id"],
                    "pipeline_name": f"{kwargs['job_id']}_pipeline",
                    "status": "succeeded",
                    "exit_code": 0,
                    "artifact_dir": f"/tmp/artifacts/{kwargs['job_id']}",
                    "metadata_path": f"/tmp/artifacts/{kwargs['job_id']}/metadata.json",
                    "stdout_path": f"/tmp/artifacts/{kwargs['job_id']}/stdout.txt",
                    "stderr_path": f"/tmp/artifacts/{kwargs['job_id']}/stderr.log",
                    "stdout_json_path": "",
                }

            report = build_manual_local_ingest_smoke_report(
                repo_root=repo_root,
                runtime_root=runtime_path,
                execute=True,
                timeout_seconds=77,
                python_executable="/usr/bin/python3",
                runner=runner,
            )

            self.assertEqual(report["smoke_status"], "passed")
            self.assertEqual([call["job_id"] for call in calls], ["market-price-daily", "news-rss-daily", "event-intelligence-weekly"])
            self.assertTrue(all(call["timeout_seconds"] == 77 for call in calls))
            self.assertEqual(len(report["artifact_runs"]), 3)

    def test_failed_artifact_run_marks_report_failed(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = _write_runtime_env(Path(runtime_root))

            def runner(**kwargs: object) -> dict[str, object]:
                return {
                    "job_id": kwargs["job_id"],
                    "pipeline_name": f"{kwargs['job_id']}_pipeline",
                    "status": "failed",
                    "exit_code": 9,
                    "artifact_dir": f"/tmp/artifacts/{kwargs['job_id']}",
                    "metadata_path": f"/tmp/artifacts/{kwargs['job_id']}/metadata.json",
                    "stdout_path": f"/tmp/artifacts/{kwargs['job_id']}/stdout.txt",
                    "stderr_path": f"/tmp/artifacts/{kwargs['job_id']}/stderr.log",
                    "stdout_json_path": "",
                }

            report = build_manual_local_ingest_smoke_report(
                repo_root=repo_root,
                runtime_root=runtime_path,
                job_ids=("market-price-daily",),
                execute=True,
                runner=runner,
            )

            self.assertEqual(report["smoke_status"], "failed")
            self.assertEqual(report["failed_job_count"], 1)
            self.assertIn("inspect failed artifact", " ".join(report["next_actions"]))

    def test_runtime_venv_python_is_preferred_for_local_execution(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = _write_runtime_env(Path(runtime_root))
            runtime_python = (runtime_path / "venv" / "bin" / "python").resolve()
            runtime_python.parent.mkdir(parents=True)
            runtime_python.write_text("#!/usr/bin/env python\n", encoding="utf-8")

            report = build_manual_local_ingest_smoke_report(
                repo_root=repo_root,
                runtime_root=runtime_path,
                job_ids=("market-price-daily",),
            )

            self.assertEqual(report["python_executable"], str(runtime_python))
            command = report["planned_jobs"][0]["command_argv"]
            self.assertEqual(command[0], str(runtime_python))

    def test_unsupported_job_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                build_manual_local_ingest_job(
                    job_id="unknown-job",
                    data_operations_env_file=Path(tmpdir) / "data-operations.env",
                )

    def test_repo_inside_env_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            repo_path = Path(repo_root)
            env_file = repo_path / "data-operations.env"
            env_file.write_text("STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT=/tmp/artifacts\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                build_manual_local_ingest_smoke_report(
                    repo_root=repo_path,
                    runtime_root=repo_path,
                    data_operations_env_file=env_file,
                )

    def test_visibility_report_returns_not_configured_without_path(self) -> None:
        report = load_manual_local_ingest_smoke_visibility_report(env={})

        self.assertEqual(report["status"], "not_configured")
        self.assertEqual(report["source"], "not_configured")
        self.assertEqual(report["planned_job_ids"], [])

    def test_visibility_report_loads_sanitized_summary(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = _write_runtime_env(Path(runtime_root))
            summary_path = runtime_path / "manual-smoke.json"
            smoke_report = build_manual_local_ingest_smoke_report(
                repo_root=repo_root,
                runtime_root=runtime_path,
                job_ids=("market-price-daily", "news-rss-daily"),
                execute=False,
                python_executable="/usr/bin/python3",
            )
            summary_path.write_text(json.dumps(smoke_report), encoding="utf-8")

            visibility = load_manual_local_ingest_smoke_visibility_report(
                report_path=summary_path,
                repo_root=repo_root,
            )

            self.assertEqual(visibility["status"], "preview_not_executed")
            self.assertFalse(visibility["execute"])
            self.assertEqual(visibility["planned_job_ids"], ["market-price-daily", "news-rss-daily"])
            self.assertEqual(visibility["job_count"], 2)
            visibility_text = json.dumps(visibility)
            self.assertNotIn("hidden-db-password", visibility_text)
            self.assertNotIn("hidden-twelve-key", visibility_text)
            self.assertNotIn("postgresql://", visibility_text)
            self.assertNotIn("data-operations.env", visibility_text)
            self.assertNotIn("python_executable", visibility_text)

    def test_visibility_report_rejects_repo_inside_path(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            report_path = Path(repo_root) / "manual-smoke.json"
            report_path.write_text(
                json.dumps({"report_name": "manual_local_ingest_smoke", "smoke_status": "passed"}),
                encoding="utf-8",
            )

            visibility = load_manual_local_ingest_smoke_visibility_report(
                report_path=report_path,
                repo_root=repo_root,
            )

            self.assertEqual(visibility["status"], "invalid_report")
            self.assertEqual(visibility["source"], "invalid_report")

    def test_visibility_report_marks_missing_path(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            visibility = load_manual_local_ingest_smoke_visibility_report(
                report_path=Path(repo_root).parent / "missing-manual-smoke.json",
                repo_root=repo_root,
            )

            self.assertEqual(visibility["status"], "missing_report")
            self.assertEqual(visibility["source"], "missing_report")


def _write_runtime_env(runtime_path: Path) -> Path:
    artifact_root = runtime_path / "artifacts"
    artifact_root.mkdir(parents=True)
    data_env = runtime_path / "data-operations.env"
    frontend_env = runtime_path / "frontend-api.env"
    data_env.write_text(
        "\n".join(
            [
                'STOCKANALYSIS_DATABASE_URL="postgresql://user:hidden-db-password@localhost/db"',
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"',
                'STOCKANALYSIS_TWELVE_DATA_API_KEY="hidden-twelve-key"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    frontend_env.write_text('STOCKANALYSIS_DATABASE_URL="postgresql://user:hidden-db-password@localhost/db"\n', encoding="utf-8")
    return runtime_path


if __name__ == "__main__":
    unittest.main()
