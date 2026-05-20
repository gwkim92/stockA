from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stockanalysis.operations.local_ingest_worker import run_local_ingest_worker
from stockanalysis.operations.local_ingest_worker import load_local_ingest_worker_visibility_report


class LocalIngestWorkerTests(unittest.TestCase):
    def test_preview_runs_one_secret_free_cycle_and_writes_latest_smoke_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            smoke_output = Path(outside_root) / "manual-local-ingest-smoke.json"
            calls: list[dict[str, object]] = []

            def smoke_builder(**kwargs: object) -> dict[str, object]:
                calls.append(dict(kwargs))
                return _smoke_report(status="preview_not_executed", execute=False)

            report = run_local_ingest_worker(
                repo_root=repo_root,
                runtime_root=outside_root,
                job_ids=("market-price-daily",),
                smoke_output_path=smoke_output,
                smoke_builder=smoke_builder,
            )

            self.assertEqual(report["report_name"], "local_ingest_worker")
            self.assertEqual(report["worker_status"], "preview_not_executed")
            self.assertFalse(report["execute"])
            self.assertEqual(report["completed_cycle_count"], 1)
            self.assertEqual(len(calls), 1)
            self.assertFalse(calls[0]["execute"])
            self.assertTrue(smoke_output.is_file())
            self.assertEqual(json.loads(smoke_output.read_text(encoding="utf-8"))["report_name"], "manual_local_ingest_smoke")
            self.assertFalse(report["codex_host_mutation_allowed"])
            self.assertFalse(report["launchagents_install_allowed"])
            self.assertNotIn("hidden-", json.dumps(report))

    def test_execute_runs_bounded_cycles_and_sleeps_between_cycles(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            calls: list[dict[str, object]] = []
            sleeps: list[float] = []

            def smoke_builder(**kwargs: object) -> dict[str, object]:
                calls.append(dict(kwargs))
                return _smoke_report(status="passed", execute=True)

            report = run_local_ingest_worker(
                repo_root=repo_root,
                runtime_root=outside_root,
                job_ids=("market-price-daily", "news-rss-daily"),
                execute=True,
                max_cycles=2,
                interval_seconds=3.5,
                timeout_seconds=77,
                smoke_builder=smoke_builder,
                sleep_fn=sleeps.append,
            )

            self.assertEqual(report["worker_status"], "completed")
            self.assertEqual(report["completed_cycle_count"], 2)
            self.assertEqual(len(calls), 2)
            self.assertEqual(sleeps, [3.5])
            self.assertTrue(all(call["execute"] is True for call in calls))
            self.assertTrue(all(call["timeout_seconds"] == 77 for call in calls))
            self.assertEqual(calls[0]["job_ids"], ("market-price-daily", "news-rss-daily"))

    def test_failure_stops_next_cycle_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            calls: list[dict[str, object]] = []

            def smoke_builder(**kwargs: object) -> dict[str, object]:
                calls.append(dict(kwargs))
                return _smoke_report(status="failed", execute=True, failed_job_count=1)

            report = run_local_ingest_worker(
                repo_root=repo_root,
                runtime_root=outside_root,
                execute=True,
                max_cycles=3,
                smoke_builder=smoke_builder,
                sleep_fn=lambda seconds: None,
            )

            self.assertEqual(report["worker_status"], "failed")
            self.assertEqual(report["completed_cycle_count"], 1)
            self.assertEqual(report["failed_cycle_count"], 1)
            self.assertEqual(len(calls), 1)

    def test_continue_on_failure_keeps_bounded_cycles(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            calls: list[dict[str, object]] = []

            def smoke_builder(**kwargs: object) -> dict[str, object]:
                calls.append(dict(kwargs))
                return _smoke_report(status="failed", execute=True, failed_job_count=1)

            report = run_local_ingest_worker(
                repo_root=repo_root,
                runtime_root=outside_root,
                execute=True,
                max_cycles=2,
                stop_on_failure=False,
                smoke_builder=smoke_builder,
                sleep_fn=lambda seconds: None,
            )

            self.assertEqual(report["worker_status"], "failed")
            self.assertEqual(report["completed_cycle_count"], 2)
            self.assertEqual(report["failed_cycle_count"], 2)
            self.assertEqual(len(calls), 2)

    def test_repo_inside_smoke_output_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            with self.assertRaises(ValueError):
                run_local_ingest_worker(
                    repo_root=repo_root,
                    runtime_root=outside_root,
                    smoke_output_path=Path(repo_root) / "manual-smoke.json",
                    smoke_builder=lambda **kwargs: _smoke_report(status="preview_not_executed", execute=False),
                )

    def test_invalid_loop_values_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            with self.assertRaises(ValueError):
                run_local_ingest_worker(repo_root=repo_root, runtime_root=outside_root, max_cycles=0)
            with self.assertRaises(ValueError):
                run_local_ingest_worker(repo_root=repo_root, runtime_root=outside_root, interval_seconds=-1)
            with self.assertRaises(ValueError):
                run_local_ingest_worker(repo_root=repo_root, runtime_root=outside_root, timeout_seconds=0)

    def test_visibility_report_returns_not_configured_without_path(self) -> None:
        report = load_local_ingest_worker_visibility_report(env={})

        self.assertEqual(report["status"], "not_configured")
        self.assertEqual(report["source"], "not_configured")
        self.assertEqual(report["job_ids"], [])

    def test_visibility_report_loads_sanitized_worker_summary(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            worker_report_path = Path(outside_root) / "local-worker.json"
            worker_report = run_local_ingest_worker(
                repo_root=repo_root,
                runtime_root=outside_root,
                job_ids=("market-price-daily",),
                execute=True,
                max_cycles=1,
                smoke_output_path=Path(outside_root) / "manual-smoke.json",
                smoke_builder=lambda **kwargs: _smoke_report(status="passed", execute=True),
            )
            worker_report_path.write_text(json.dumps(worker_report), encoding="utf-8")

            visibility = load_local_ingest_worker_visibility_report(
                report_path=worker_report_path,
                repo_root=repo_root,
            )

            self.assertEqual(visibility["status"], "completed")
            self.assertTrue(visibility["execute"])
            self.assertEqual(visibility["completed_cycle_count"], 1)
            self.assertEqual(visibility["failed_cycle_count"], 0)
            self.assertEqual(visibility["job_ids"], ["market-price-daily"])
            self.assertEqual(visibility["source"], "local_ingest_worker_report")
            self.assertEqual(visibility["cycles"][0]["smoke_status"], "passed")
            visibility_text = json.dumps(visibility)
            self.assertNotIn("hidden-", visibility_text)
            self.assertNotIn("postgresql://", visibility_text)

    def test_visibility_report_rejects_repo_inside_path(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            report_path = Path(repo_root) / "worker.json"
            report_path.write_text(json.dumps({"report_name": "local_ingest_worker"}), encoding="utf-8")

            visibility = load_local_ingest_worker_visibility_report(
                report_path=report_path,
                repo_root=repo_root,
            )

            self.assertEqual(visibility["status"], "invalid_report")
            self.assertEqual(visibility["source"], "invalid_report")

    def test_visibility_report_marks_missing_path(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            visibility = load_local_ingest_worker_visibility_report(
                report_path=Path(repo_root).parent / "missing-worker.json",
                repo_root=repo_root,
            )

            self.assertEqual(visibility["status"], "missing_report")
            self.assertEqual(visibility["source"], "missing_report")


def _smoke_report(*, status: str, execute: bool, failed_job_count: int = 0) -> dict[str, object]:
    return {
        "report_name": "manual_local_ingest_smoke",
        "smoke_status": status,
        "runtime_status": "ready",
        "execute": execute,
        "job_count": 1,
        "failed_job_count": failed_job_count,
        "artifact_runs": [
            {
                "job_id": "market-price-daily",
                "status": "succeeded" if failed_job_count == 0 else "failed",
                "exit_code": 0 if failed_job_count == 0 else 1,
            }
        ]
        if execute
        else [],
    }


if __name__ == "__main__":
    unittest.main()
