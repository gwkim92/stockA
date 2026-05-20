from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stockanalysis.operations.server_scheduler_invocation import (
    SERVER_SCHEDULER_TARGETS,
    build_server_scheduler_invocation_plan,
    render_server_scheduler_invocation_markdown,
)


class ServerSchedulerInvocationTests(unittest.TestCase):
    def test_cron_plan_builds_secret_free_preview_without_execution(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = _runtime_env(Path(outside_root))

            report = build_server_scheduler_invocation_plan(
                scheduler_target="cron",
                repo_root=repo_root,
                runtime_root=Path(outside_root) / "runtime",
                data_operations_env_file=env_file,
                worker_report_output=Path(outside_root) / "worker.json",
                smoke_output=Path(outside_root) / "manual-smoke.json",
                artifact_root=Path(outside_root) / "artifacts",
                job_ids=("market-price-daily",),
                python_executable="/usr/bin/python3",
            )

            self.assertEqual(report["report_name"], "server_scheduler_invocation_boundary")
            self.assertEqual(report["scheduler_target"], "cron")
            self.assertFalse(report["scheduler_deployed"])
            self.assertFalse(report["scheduler_install_allowed_in_this_task"])
            self.assertFalse(report["host_mutation_allowed"])
            self.assertFalse(report["launchctl_executed"])
            self.assertFalse(report["child_command_executed"])
            self.assertFalse(report["worker_execute"])
            self.assertIn("local-ingest-worker-run", report["shell_command_preview"])
            self.assertNotIn("--execute", report["command_argv_preview"])
            self.assertEqual(report["target_manifest_preview"]["kind"], "crontab_line_preview")
            self.assertNotIn("hidden-pass", json.dumps(report))
            self.assertNotIn("postgresql://", json.dumps(report))

    def test_worker_execute_is_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            report = build_server_scheduler_invocation_plan(
                scheduler_target="systemd",
                repo_root=repo_root,
                runtime_root=Path(outside_root) / "runtime",
                data_operations_env_file=_runtime_env(Path(outside_root)),
                worker_report_output=Path(outside_root) / "worker.json",
                smoke_output=Path(outside_root) / "manual-smoke.json",
                worker_execute=True,
                schedule="Mon-Fri 18:30:00",
            )

            self.assertTrue(report["worker_execute"])
            self.assertIn("--execute", report["command_argv_preview"])
            self.assertEqual(report["target_manifest_preview"]["kind"], "systemd_unit_timer_preview")

    def test_all_targets_render_manifest_preview(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = _runtime_env(Path(outside_root))

            for target in SERVER_SCHEDULER_TARGETS:
                with self.subTest(target=target):
                    report = build_server_scheduler_invocation_plan(
                        scheduler_target=target,
                        repo_root=repo_root,
                        runtime_root=Path(outside_root) / "runtime",
                        data_operations_env_file=env_file,
                        worker_report_output=Path(outside_root) / f"{target}-worker.json",
                        smoke_output=Path(outside_root) / f"{target}-smoke.json",
                    )

                    self.assertEqual(report["scheduler_target"], target)
                    self.assertIn("target_manifest_preview", report)
                    self.assertFalse(report["scheduler_deployed"])

    def test_repo_inside_env_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(repo_root) / "data-operations.env"
            env_file.write_text("", encoding="utf-8")

            with self.assertRaises(ValueError):
                build_server_scheduler_invocation_plan(
                    scheduler_target="cron",
                    repo_root=repo_root,
                    runtime_root=Path(outside_root) / "runtime",
                    data_operations_env_file=env_file,
                    worker_report_output=Path(outside_root) / "worker.json",
                    smoke_output=Path(outside_root) / "manual-smoke.json",
                )

    def test_repo_inside_outputs_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            with self.assertRaises(ValueError):
                build_server_scheduler_invocation_plan(
                    scheduler_target="cron",
                    repo_root=repo_root,
                    runtime_root=Path(outside_root) / "runtime",
                    data_operations_env_file=_runtime_env(Path(outside_root)),
                    worker_report_output=Path(repo_root) / "worker.json",
                    smoke_output=Path(outside_root) / "manual-smoke.json",
                )

    def test_invalid_values_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            kwargs = {
                "repo_root": repo_root,
                "runtime_root": Path(outside_root) / "runtime",
                "data_operations_env_file": _runtime_env(Path(outside_root)),
                "worker_report_output": Path(outside_root) / "worker.json",
                "smoke_output": Path(outside_root) / "manual-smoke.json",
            }
            with self.assertRaises(ValueError):
                build_server_scheduler_invocation_plan(scheduler_target="launchctl", **kwargs)
            with self.assertRaises(ValueError):
                build_server_scheduler_invocation_plan(scheduler_target="cron", max_cycles=0, **kwargs)
            with self.assertRaises(ValueError):
                build_server_scheduler_invocation_plan(scheduler_target="cron", interval_seconds=-1, **kwargs)
            with self.assertRaises(ValueError):
                build_server_scheduler_invocation_plan(scheduler_target="cron", timeout_seconds=0, **kwargs)

    def test_markdown_renderer_keeps_boundary_visible(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            report = build_server_scheduler_invocation_plan(
                scheduler_target="managed_scheduler",
                repo_root=repo_root,
                runtime_root=Path(outside_root) / "runtime",
                data_operations_env_file=_runtime_env(Path(outside_root)),
                worker_report_output=Path(outside_root) / "worker.json",
                smoke_output=Path(outside_root) / "manual-smoke.json",
            )

            markdown = render_server_scheduler_invocation_markdown(report)

            self.assertIn("Server Scheduler Invocation Boundary", markdown)
            self.assertIn("local-ingest-worker-run", markdown)
            self.assertIn("does not deploy a scheduler", markdown)
            self.assertNotIn("postgresql://", markdown)


def _runtime_env(outside_root: Path) -> Path:
    env_file = outside_root / "data-operations.env"
    env_file.write_text(
        "\n".join(
            [
                'STOCKANALYSIS_DATABASE_URL="postgresql://user:hidden-pass@localhost/db"',
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{outside_root / "artifacts"}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return env_file


if __name__ == "__main__":
    unittest.main()
