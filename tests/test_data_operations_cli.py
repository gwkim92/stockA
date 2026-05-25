from __future__ import annotations

import io
import json
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from stockanalysis.operations.cli import main
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.operations.path_policy import resolve_existing_file, resolve_output_path


class DataOperationsCliTests(unittest.TestCase):
    def test_cadence_command_prints_backend_report(self) -> None:
        stdout = io.StringIO()

        exit_code = main(["cadence", "--cadence", "weekly"], stdout=stdout)

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["report_name"], "data_operations_cadence_foundation")
        self.assertEqual(payload["cadence_filter"], "weekly")

    def test_local_runtime_status_command_prints_secret_free_report(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = Path(runtime_root)
            artifact_root = runtime_path / "artifacts"
            artifact_root.mkdir()
            (runtime_path / "frontend-api.env").write_text(
                'STOCKANALYSIS_DATABASE_URL="postgresql://user:hidden-cli-pass@localhost/db"\n',
                encoding="utf-8",
            )
            (runtime_path / "data-operations.env").write_text(
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"\n',
                encoding="utf-8",
            )
            stdout = io.StringIO()

            exit_code = main(
                [
                    "local-runtime-status",
                    "--repo-root",
                    repo_root,
                    "--runtime-root",
                    runtime_root,
                    "--skip-http-probes",
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "local_first_runtime_status")
            self.assertFalse(payload["codex_host_mutation_allowed"])
            self.assertNotIn("hidden-cli-pass", stdout.getvalue())

    def test_manual_local_ingest_smoke_preview_command_is_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = Path(runtime_root)
            artifact_root = runtime_path / "artifacts"
            artifact_root.mkdir()
            (runtime_path / "data-operations.env").write_text(
                "\n".join(
                    [
                        'STOCKANALYSIS_DATABASE_URL="postgresql://user:hidden-smoke-pass@localhost/db"',
                        f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (runtime_path / "frontend-api.env").write_text("", encoding="utf-8")
            stdout = io.StringIO()

            exit_code = main(
                [
                    "manual-local-ingest-smoke",
                    "--repo-root",
                    repo_root,
                    "--runtime-root",
                    runtime_root,
                    "--job-id",
                    "market-price-daily",
                    "--python-executable",
                    "/usr/bin/python3",
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "manual_local_ingest_smoke")
            self.assertEqual(payload["smoke_status"], "preview_not_executed")
            self.assertFalse(payload["execute"])
            self.assertNotIn("hidden-smoke-pass", stdout.getvalue())

    def test_manual_local_ingest_smoke_output_writes_repo_outside_summary(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = Path(runtime_root)
            artifact_root = runtime_path / "artifacts"
            artifact_root.mkdir()
            output_path = runtime_path / "manual-smoke-summary.json"
            (runtime_path / "data-operations.env").write_text(
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"\n',
                encoding="utf-8",
            )
            (runtime_path / "frontend-api.env").write_text("", encoding="utf-8")
            stdout = io.StringIO()

            exit_code = main(
                [
                    "manual-local-ingest-smoke",
                    "--repo-root",
                    repo_root,
                    "--runtime-root",
                    runtime_root,
                    "--job-id",
                    "market-price-daily",
                    "--output",
                    str(output_path),
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_name"], "manual_local_ingest_smoke")
            self.assertEqual(payload["smoke_status"], "preview_not_executed")

    def test_manual_local_ingest_smoke_output_rejects_repo_inside_path(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = Path(runtime_root)
            artifact_root = runtime_path / "artifacts"
            artifact_root.mkdir()
            output_path = Path(repo_root) / "manual-smoke-summary.json"
            (runtime_path / "data-operations.env").write_text(
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"\n',
                encoding="utf-8",
            )
            (runtime_path / "frontend-api.env").write_text("", encoding="utf-8")
            stderr = io.StringIO()

            exit_code = main(
                [
                    "manual-local-ingest-smoke",
                    "--repo-root",
                    repo_root,
                    "--runtime-root",
                    runtime_root,
                    "--job-id",
                    "market-price-daily",
                    "--output",
                    str(output_path),
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_local_ingest_worker_run_command_passes_runtime_args_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_path = Path(outside_root) / "runtime"
            runtime_path.mkdir()
            output_path = Path(outside_root) / "worker.json"
            smoke_output_path = Path(outside_root) / "manual-smoke.json"
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_local_ingest_worker") as worker_mock:
                worker_mock.return_value = {
                    "report_name": "local_ingest_worker",
                    "worker_status": "completed",
                    "execute": True,
                }
                exit_code = main(
                    [
                        "local-ingest-worker-run",
                        "--repo-root",
                        repo_root,
                        "--runtime-root",
                        str(runtime_path),
                        "--data-operations-env-file",
                        str(Path(outside_root) / "data-operations.env"),
                        "--artifact-root",
                        str(Path(outside_root) / "artifacts"),
                        "--job-id",
                        "market-price-daily",
                        "--execute",
                        "--max-cycles",
                        "2",
                        "--interval-seconds",
                        "0.5",
                        "--timeout-seconds",
                        "77",
                        "--python-executable",
                        "/usr/bin/python3",
                        "--smoke-output",
                        str(smoke_output_path),
                        "--continue-on-failure",
                        "--output",
                        str(output_path),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_name"], "local_ingest_worker")
            call_kwargs = worker_mock.call_args.kwargs
            self.assertEqual(call_kwargs["runtime_root"], str(runtime_path))
            self.assertEqual(call_kwargs["job_ids"], ("market-price-daily",))
            self.assertTrue(call_kwargs["execute"])
            self.assertEqual(call_kwargs["max_cycles"], 2)
            self.assertEqual(call_kwargs["interval_seconds"], 0.5)
            self.assertEqual(call_kwargs["timeout_seconds"], 77)
            self.assertEqual(call_kwargs["python_executable"], "/usr/bin/python3")
            self.assertEqual(call_kwargs["smoke_output_path"], str(smoke_output_path))
            self.assertFalse(call_kwargs["stop_on_failure"])

    def test_operating_data_run_command_writes_repo_outside_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            runtime_path = Path(outside_root) / "runtime"
            env_file = Path(outside_root) / "data-operations.env"
            output_path = Path(outside_root) / "operating-data.json"
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.build_operating_data_run_report") as run_mock:
                run_mock.return_value = {
                    "report_name": "operating_data_run",
                    "run_status": "completed",
                    "execute": True,
                }
                exit_code = main(
                    [
                        "operating-data-run",
                        "--repo-root",
                        repo_root,
                        "--runtime-root",
                        str(runtime_path),
                        "--data-operations-env-file",
                        str(env_file),
                        "--artifact-root",
                        str(Path(outside_root) / "artifacts"),
                        "--profile",
                        "decision-daily",
                        "--execute",
                        "--as-of-date",
                        "2026-05-20",
                        "--python-executable",
                        "/usr/bin/python3",
                        "--portfolio-name",
                        "Long Term Paper",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--market-code",
                        "US",
                        "--universe-version",
                        "live-20260520",
                        "--output",
                        str(output_path),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_name"], "operating_data_run")
            call_kwargs = run_mock.call_args.kwargs
            self.assertEqual(call_kwargs["runtime_root"], str(runtime_path))
            self.assertEqual(str(call_kwargs["data_operations_env_file"]), str(env_file))
            self.assertEqual(call_kwargs["profile"], "decision-daily")
            self.assertTrue(call_kwargs["execute"])
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 20))

    def test_operating_data_run_output_rejects_repo_inside_path(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            stderr = io.StringIO()
            exit_code = main(
                [
                    "operating-data-run",
                    "--repo-root",
                    repo_root,
                    "--runtime-root",
                    str(Path(outside_root) / "runtime"),
                    "--data-operations-env-file",
                    str(Path(outside_root) / "data-operations.env"),
                    "--output",
                    str(Path(repo_root) / "operating-data.json"),
                ],
                stderr=stderr,
            )

        self.assertEqual(exit_code, 1)
        self.assertIn("outside repository", stderr.getvalue())

    def test_local_ingest_worker_run_rejects_repo_inside_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            stderr = io.StringIO()

            with patch("stockanalysis.operations.cli.run_local_ingest_worker") as worker_mock:
                worker_mock.return_value = {
                    "report_name": "local_ingest_worker",
                    "worker_status": "preview_not_executed",
                }
                exit_code = main(
                    [
                        "local-ingest-worker-run",
                        "--repo-root",
                        repo_root,
                        "--runtime-root",
                        str(Path(repo_root).parent),
                        "--output",
                        str(Path(repo_root) / "worker.json"),
                    ],
                    stderr=stderr,
                )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())
            worker_mock.assert_not_called()

    def test_server_scheduler_invocation_plan_command_writes_output_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            outside_path = Path(outside_root)
            env_file = outside_path / "data-operations.env"
            output_path = outside_path / "server-scheduler.json"
            markdown_path = outside_path / "server-scheduler.md"
            env_file.write_text(
                'STOCKANALYSIS_DATABASE_URL="postgresql://user:hidden-scheduler-pass@localhost/db"\n',
                encoding="utf-8",
            )
            stdout = io.StringIO()

            exit_code = main(
                [
                    "server-scheduler-invocation-plan",
                    "--repo-root",
                    repo_root,
                    "--target",
                    "kubernetes_cronjob",
                    "--schedule",
                    "30 18 * * 1-5",
                    "--runtime-root",
                    str(outside_path / "runtime"),
                    "--data-operations-env-file",
                    str(env_file),
                    "--worker-output",
                    str(outside_path / "worker.json"),
                    "--smoke-output",
                    str(outside_path / "manual-smoke.json"),
                    "--artifact-root",
                    str(outside_path / "artifacts"),
                    "--job-id",
                    "market-price-daily",
                    "--worker-execute",
                    "--output",
                    str(output_path),
                    "--markdown-output",
                    str(markdown_path),
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertEqual(payload["report_name"], "server_scheduler_invocation_boundary")
            self.assertEqual(payload["scheduler_target"], "kubernetes_cronjob")
            self.assertTrue(payload["worker_execute"])
            self.assertFalse(payload["scheduler_deployed"])
            self.assertFalse(payload["host_mutation_allowed"])
            self.assertIn("local-ingest-worker-run", payload["shell_command_preview"])
            self.assertIn("local-ingest-worker-run", markdown)
            self.assertNotIn("hidden-scheduler-pass", json.dumps(payload) + markdown)
            self.assertNotIn("postgresql://", json.dumps(payload) + markdown)

    def test_operating_data_profile_scheduler_invocation_plan_command_writes_output_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            outside_path = Path(outside_root)
            env_file = outside_path / "data-operations.env"
            output_path = outside_path / "operating-data-profile-scheduler.json"
            markdown_path = outside_path / "operating-data-profile-scheduler.md"
            env_file.write_text(
                'STOCKANALYSIS_DATABASE_URL="postgresql://user:hidden-profile-pass@localhost/db"\\n'
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{outside_path / "artifacts"}"\\n',
                encoding="utf-8",
            )
            stdout = io.StringIO()

            exit_code = main(
                [
                    "operating-data-profile-scheduler-invocation-plan",
                    "--repo-root",
                    repo_root,
                    "--target",
                    "kubernetes_cronjob",
                    "--schedule",
                    "0 8 * * 1-5",
                    "--runtime-root",
                    str(outside_path / "runtime"),
                    "--data-operations-env-file",
                    str(env_file),
                    "--profile-output-root",
                    str(outside_path / "profiles"),
                    "--profile-id",
                    "news-intraday",
                    "--include-full-recovery",
                    "--profile-id",
                    "full-recovery",
                    "--manifest-output-root",
                    str(outside_path / "manifests"),
                    "--execute",
                    "--output",
                    str(output_path),
                    "--markdown-output",
                    str(markdown_path),
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertEqual(payload["report_name"], "operating_data_profile_scheduler_invocation_boundary")
            self.assertEqual(payload["scheduler_target"], "kubernetes_cronjob")
            self.assertTrue(payload["include_full_recovery"])
            self.assertEqual(len(payload["profiles"]), 2)
            self.assertEqual(payload["profiles"][0]["profile_id"], "news-intraday")
            self.assertEqual(payload["profiles"][1]["profile_id"], "full-recovery")
            self.assertTrue(payload["operating_data_run_execute"])
            self.assertNotIn("hidden-profile-pass", json.dumps(payload) + markdown)
            self.assertNotIn("postgresql://", json.dumps(payload) + markdown)
            self.assertIn("Operating Data Profile Scheduler Invocation Boundary", markdown)
            self.assertIn("kubernetes_cronjob", markdown)
            self.assertIn(str((outside_path / "manifests").resolve()), payload["manifest_output_root"])
            self.assertEqual(len(payload["manifest_records"]), 2)
            for profile in payload["profiles"]:
                self.assertIn("--execute", profile["command_argv_preview"])
                self.assertTrue(profile["manifest_file_previews"])
                for manifest_file_preview in profile["manifest_file_previews"]:
                    self.assertTrue(Path(manifest_file_preview["path"]).is_file())

    def test_server_scheduler_invocation_plan_rejects_repo_inside_env(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(repo_root) / "data-operations.env"
            env_file.write_text("", encoding="utf-8")
            stderr = io.StringIO()

            exit_code = main(
                [
                    "server-scheduler-invocation-plan",
                    "--repo-root",
                    repo_root,
                    "--target",
                    "cron",
                    "--data-operations-env-file",
                    str(env_file),
                    "--worker-output",
                    str(Path(outside_root) / "worker.json"),
                    "--smoke-output",
                    str(Path(outside_root) / "manual-smoke.json"),
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_operating_data_profile_scheduler_invocation_plan_rejects_repo_inside_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            stderr = io.StringIO()
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text("", encoding="utf-8")

            exit_code = main(
                [
                    "operating-data-profile-scheduler-invocation-plan",
                    "--repo-root",
                    repo_root,
                    "--target",
                    "cron",
                    "--runtime-root",
                    str(Path(outside_root) / "runtime"),
                    "--data-operations-env-file",
                    str(env_file),
                    "--output",
                    str(Path(repo_root) / "operating-data-profile-scheduler.json"),
                    "--profile-id",
                    "news-intraday",
                    "--include-full-recovery",
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_operating_data_profile_scheduler_invocation_plan_rejects_repo_inside_manifest_output_root(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            stderr = io.StringIO()
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text("", encoding="utf-8")

            exit_code = main(
                [
                    "operating-data-profile-scheduler-invocation-plan",
                    "--repo-root",
                    repo_root,
                    "--target",
                    "cron",
                    "--runtime-root",
                    str(Path(outside_root) / "runtime"),
                    "--data-operations-env-file",
                    str(env_file),
                    "--manifest-output-root",
                    str(Path(repo_root) / "manifests"),
                    "--profile-id",
                    "news-intraday",
                    "--include-full-recovery",
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_operating_data_profile_scheduler_status_report_command_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            output_path = Path(outside_root) / "profile-scheduler-status.json"
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.build_operating_data_profile_scheduler_status_report") as status_mock:
                status_mock.return_value = {
                    "report_name": "operating_data_profile_scheduler_status",
                    "install_status": "installed",
                    "timer_count": 7,
                }
                exit_code = main(
                    [
                        "operating-data-profile-scheduler-status-report",
                        "--repo-root",
                        repo_root,
                        "--profile-id",
                        "news-intraday",
                        "--job-name",
                        "stockanalysis-operating-data",
                        "--output",
                        str(output_path),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_name"], "operating_data_profile_scheduler_status")
            self.assertEqual(payload["timer_count"], 7)
            status_mock.assert_called_once()
            self.assertEqual(status_mock.call_args.kwargs["profile_ids"], ("news-intraday",))

    def test_server_scheduler_deployment_target_decision_command_writes_output_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            output_path = Path(outside_root) / "scheduler-decision.json"
            markdown_path = Path(outside_root) / "scheduler-decision.md"
            stdout = io.StringIO()

            exit_code = main(
                [
                    "server-scheduler-deployment-target-decision",
                    "--repo-root",
                    repo_root,
                    "--repo-visibility",
                    "public",
                    "--output",
                    str(output_path),
                    "--markdown-output",
                    str(markdown_path),
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertEqual(payload["report_name"], "server_scheduler_deployment_target_decision")
            self.assertEqual(payload["decision_status"], "blocked_missing_hosted_database_or_runtime")
            self.assertEqual(
                payload["recommended_target"],
                "github_actions_scheduled_workflow_after_hosted_runtime",
            )
            self.assertFalse(payload["scheduler_deployed"])
            self.assertFalse(payload["workflow_file_created"])
            self.assertIn("Server Scheduler Deployment Target Decision", markdown)
            self.assertNotIn("postgresql://", json.dumps(payload) + markdown)

    def test_server_scheduler_deployment_target_decision_rejects_repo_inside_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            stderr = io.StringIO()

            exit_code = main(
                [
                    "server-scheduler-deployment-target-decision",
                    "--repo-root",
                    repo_root,
                    "--output",
                    str(Path(repo_root) / "scheduler-decision.json"),
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_hosted_database_runtime_decision_command_writes_output_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            output_path = Path(outside_root) / "hosted-runtime-decision.json"
            markdown_path = Path(outside_root) / "hosted-runtime-decision.md"
            stdout = io.StringIO()

            exit_code = main(
                [
                    "hosted-database-runtime-decision",
                    "--repo-root",
                    repo_root,
                    "--repo-visibility",
                    "public",
                    "--output",
                    str(output_path),
                    "--markdown-output",
                    str(markdown_path),
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")
            self.assertEqual(payload["report_name"], "hosted_database_runtime_decision")
            self.assertEqual(payload["decision_status"], "setup_required_for_hosted_database")
            self.assertEqual(payload["recommended_path"], "supabase_free_postgres_plus_github_actions_worker")
            self.assertFalse(payload["provisioning_performed"])
            self.assertFalse(payload["database_created"])
            self.assertFalse(payload["secret_written"])
            self.assertFalse(payload["workflow_file_created"])
            self.assertIn("Hosted Database Runtime Decision", markdown)
            self.assertNotIn("postgresql://", json.dumps(payload) + markdown)

    def test_hosted_database_runtime_decision_rejects_repo_inside_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            stderr = io.StringIO()

            exit_code = main(
                [
                    "hosted-database-runtime-decision",
                    "--repo-root",
                    repo_root,
                    "--output",
                    str(Path(repo_root) / "hosted-runtime-decision.json"),
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_host_activation_execution_decision_command_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            request_path = Path(outside_root) / "execution-request.json"
            output_path = Path(outside_root) / "nested" / "execution-decision.json"
            request_path.write_text(json.dumps(_execution_request_report()), encoding="utf-8")
            stdout = io.StringIO()

            exit_code = main(
                [
                    "host-activation-execution-decision",
                    "--repo-root",
                    repo_root,
                    "--execution-request-report",
                    str(request_path),
                    "--output",
                    str(output_path),
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["decision_gate"], "blocked_pending_execution_decision")
            self.assertEqual(payload["execution_request_report_path"], str(request_path.resolve()))

    def test_host_activation_execution_decision_command_rejects_repo_inside_report(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            request_path = Path(repo_root) / "execution-request.json"
            request_path.write_text(json.dumps(_execution_request_report()), encoding="utf-8")
            stderr = io.StringIO()

            exit_code = main(
                [
                    "host-activation-execution-decision",
                    "--repo-root",
                    repo_root,
                    "--execution-request-report",
                    str(request_path),
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_manual_host_scheduler_activation_explicit_approval_command_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            host_report_path = Path(outside_root) / "host-activation-execution.json"
            output_path = Path(outside_root) / "nested" / "manual-approval.json"
            host_report_path.write_text(json.dumps(_host_activation_execution_report()), encoding="utf-8")
            stdout = io.StringIO()

            exit_code = main(
                [
                    "manual-host-scheduler-activation-explicit-approval",
                    "--repo-root",
                    repo_root,
                    "--host-activation-execution-report",
                    str(host_report_path),
                    "--output",
                    str(output_path),
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["approval_gate"], "blocked_pending_exact_host_command_approval")
            self.assertEqual(payload["host_activation_execution_report_path"], str(host_report_path.resolve()))

    def test_manual_host_scheduler_activation_explicit_approval_rejects_repo_inside_report(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            host_report_path = Path(repo_root) / "host-activation-execution.json"
            host_report_path.write_text(json.dumps(_host_activation_execution_report()), encoding="utf-8")
            stderr = io.StringIO()

            exit_code = main(
                [
                    "manual-host-scheduler-activation-explicit-approval",
                    "--repo-root",
                    repo_root,
                    "--host-activation-execution-report",
                    str(host_report_path),
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_manual_host_scheduler_activation_preflight_command_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            approval_path = Path(outside_root) / "manual-approval.json"
            output_dir = Path(outside_root) / "preflight"
            env_file = _write_runtime_env_file(Path(outside_root))
            approval_path.write_text(json.dumps(_manual_approval_report()), encoding="utf-8")
            stdout = io.StringIO()

            exit_code = main(
                [
                    "manual-host-scheduler-activation-preflight",
                    "--repo-root",
                    repo_root,
                    "--manual-approval-report",
                    str(approval_path),
                    "--env-file",
                    str(env_file),
                    "--output-dir",
                    str(output_dir),
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            preflight_path = output_dir / "manual-host-scheduler-activation-preflight.json"
            self.assertEqual(stdout.getvalue().strip(), str(preflight_path.resolve()))
            payload = json.loads(preflight_path.read_text(encoding="utf-8"))
            self.assertEqual(
                payload["manual_activation_preflight"],
                "passed_ready_for_external_manual_host_scheduler_activation",
            )
            self.assertFalse(payload["codex_host_mutation_allowed"])
            self.assertTrue((output_dir / "evidence" / "runtime-env-readiness.json").is_file())

    def test_manual_host_scheduler_activation_preflight_rejects_repo_inside_env(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            approval_path = Path(outside_root) / "manual-approval.json"
            approval_path.write_text(json.dumps(_manual_approval_report()), encoding="utf-8")
            env_file = Path(repo_root) / "data-operations.env"
            env_file.write_text("", encoding="utf-8")
            stderr = io.StringIO()

            exit_code = main(
                [
                    "manual-host-scheduler-activation-preflight",
                    "--repo-root",
                    repo_root,
                    "--manual-approval-report",
                    str(approval_path),
                    "--env-file",
                    str(env_file),
                    "--output-dir",
                    str(Path(outside_root) / "preflight"),
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_market_price_free_backfill_run_command_passes_budget_args_and_env(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            outside_path = Path(outside_root)
            watchlist = outside_path / "watchlist.csv"
            watchlist.write_text("symbol\nAAPL\nMSFT\n", encoding="utf-8")
            ledger = outside_path / "ledger.json"
            env_file = outside_path / "data-operations.env"
            env_file.write_text(
                "\n".join(
                    [
                        'STOCKANALYSIS_PSQL_COMMAND="docker exec psql"',
                        'STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-key-12345"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_market_price_free_backfill") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "market_price_free_backfill_run",
                    "status": "no_provider_request_budget",
                    "failed_symbol_count": 0,
                    "provider_request_count": 0,
                }
                exit_code = main(
                    [
                        "market-price-free-backfill-run",
                        "--repo-root",
                        repo_root,
                        "--watchlist",
                        str(watchlist),
                        "--ledger",
                        str(ledger),
                        "--provider",
                        "twelve_data",
                        "--env-file",
                        str(env_file),
                        "--daily-budget",
                        "1",
                        "--max-requests-per-run",
                        "0",
                        "--throttle-seconds",
                        "1.5",
                        "--outputsize",
                        "compact",
                        "--budget-date",
                        "2026-05-17",
                        "--skip-if-fresh",
                        "--freshness-date",
                        "2026-05-15",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "market_price_free_backfill_run")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["provider"], "twelve_data")
            self.assertEqual(call_kwargs["daily_budget"], 1)
            self.assertEqual(call_kwargs["max_requests_per_run"], 0)
            self.assertEqual(call_kwargs["throttle_seconds"], 1.5)
            self.assertEqual(call_kwargs["outputsize"], "compact")
            self.assertTrue(call_kwargs["skip_if_fresh"])
            self.assertEqual(call_kwargs["freshness_date"].isoformat(), "2026-05-15")

    def test_market_price_free_backfill_run_allows_symbol_failures_only_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            outside_path = Path(outside_root)
            watchlist = outside_path / "watchlist.csv"
            watchlist.write_text("symbol\nBRK-A\n", encoding="utf-8")
            ledger = outside_path / "ledger.json"
            env_file = outside_path / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")

            with patch("stockanalysis.operations.cli.run_market_price_free_backfill") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "market_price_free_backfill_run",
                    "status": "completed",
                    "failed_symbol_count": 1,
                    "provider_request_count": 1,
                    "results": [
                        {
                            "symbol": "BRK-A",
                            "status": "failed",
                            "error": "provider rejected symbol",
                        }
                    ],
                }
                strict_stdout = io.StringIO()
                strict_exit = main(
                    [
                        "market-price-free-backfill-run",
                        "--repo-root",
                        repo_root,
                        "--watchlist",
                        str(watchlist),
                        "--ledger",
                        str(ledger),
                        "--env-file",
                        str(env_file),
                    ],
                    stdout=strict_stdout,
                )

            self.assertEqual(strict_exit, 1)
            self.assertEqual(json.loads(strict_stdout.getvalue())["failed_symbol_count"], 1)

            with patch("stockanalysis.operations.cli.run_market_price_free_backfill") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "market_price_free_backfill_run",
                    "status": "completed",
                    "failed_symbol_count": 1,
                    "provider_request_count": 1,
                    "results": [
                        {
                            "symbol": "BRK-A",
                            "status": "failed",
                            "error": "provider rejected symbol",
                        }
                    ],
                }
                tolerant_stdout = io.StringIO()
                tolerant_exit = main(
                    [
                        "market-price-free-backfill-run",
                        "--repo-root",
                        repo_root,
                        "--watchlist",
                        str(watchlist),
                        "--ledger",
                        str(ledger),
                        "--env-file",
                        str(env_file),
                        "--allow-symbol-failures",
                    ],
                    stdout=tolerant_stdout,
                )

            self.assertEqual(tolerant_exit, 0)
            payload = json.loads(tolerant_stdout.getvalue())
            self.assertEqual(payload["failed_symbol_count"], 1)
            self.assertTrue(payload["symbol_failures_allowed"])
            self.assertEqual(payload["results"][0]["symbol"], "BRK-A")

    def test_market_price_free_backfill_run_rejects_repo_inside_watchlist(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            watchlist = Path(repo_root) / "watchlist.csv"
            watchlist.write_text("symbol\nAAPL\n", encoding="utf-8")
            ledger = Path(outside_root) / "ledger.json"
            stderr = io.StringIO()

            exit_code = main(
                [
                    "market-price-free-backfill-run",
                    "--repo-root",
                    repo_root,
                    "--watchlist",
                    str(watchlist),
                    "--ledger",
                    str(ledger),
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_market_price_daily_run_command_reads_scheduler_env_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            outside_path = Path(outside_root)
            watchlist = outside_path / "watchlist.csv"
            watchlist.write_text("symbol\nAAPL\n", encoding="utf-8")
            ledger = outside_path / "ledger.json"
            env_file = outside_path / "data-operations.env"
            env_file.write_text(
                "\n".join(
                    [
                        'STOCKANALYSIS_PSQL_COMMAND="docker exec psql"',
                        'STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"',
                        'STOCKANALYSIS_TWELVE_DATA_API_KEY="twelve-key-12345"',
                        f'STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV="{watchlist}"',
                        f'STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="{ledger}"',
                        'STOCKANALYSIS_MARKET_PRICE_DAILY_BUDGET="800"',
                        'STOCKANALYSIS_MARKET_PRICE_MAX_REQUESTS_PER_RUN="50"',
                        'STOCKANALYSIS_MARKET_PRICE_THROTTLE_SECONDS="8"',
                        'STOCKANALYSIS_MARKET_PRICE_OUTPUTSIZE="100"',
                        'DATA_OPERATIONS_SCHEDULER_RUN_DATE="2026-05-18"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_market_price_daily_from_env") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "market_price_free_backfill_run",
                    "status": "completed",
                    "failed_symbol_count": 0,
                    "provider_request_count": 0,
                }
                exit_code = main(
                    [
                        "market-price-daily-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "market_price_free_backfill_run")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertIsNone(call_kwargs["provider"])
            self.assertIsNone(call_kwargs["daily_budget"])
            self.assertTrue(call_kwargs["skip_if_fresh"])

    def test_market_price_daily_run_keeps_symbol_failures_strict(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            outside_path = Path(outside_root)
            watchlist = outside_path / "watchlist.csv"
            watchlist.write_text("symbol\nBRK-A\n", encoding="utf-8")
            ledger = outside_path / "ledger.json"
            env_file = outside_path / "data-operations.env"
            env_file.write_text(
                "\n".join(
                    [
                        'STOCKANALYSIS_PSQL_COMMAND="docker exec psql"',
                        'STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"',
                        f'STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV="{watchlist}"',
                        f'STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="{ledger}"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            with patch("stockanalysis.operations.cli.run_market_price_daily_from_env") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "market_price_free_backfill_run",
                    "status": "completed",
                    "failed_symbol_count": 1,
                    "provider_request_count": 1,
                }
                stdout = io.StringIO()
                exit_code = main(
                    [
                        "market-price-daily-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 1)
            self.assertEqual(json.loads(stdout.getvalue())["failed_symbol_count"], 1)

    def test_news_rss_config_report_prints_sanitized_feed_list(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            feed_config = _write_news_rss_feed_config(Path(outside_root))
            stdout = io.StringIO()

            exit_code = main(
                [
                    "news-rss-config-report",
                    "--repo-root",
                    repo_root,
                    "--feed-config",
                    str(feed_config),
                ],
                stdout=stdout,
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            payload_text = stdout.getvalue()
            self.assertEqual(payload["report_name"], "news_rss_feed_config")
            self.assertEqual(payload["enabled_feed_count"], 1)
            self.assertIn("example.com", payload_text)
            self.assertNotIn("https://example.com/free/rss", payload_text)

    def test_news_rss_daily_run_command_passes_env_and_config(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            outside_path = Path(outside_root)
            feed_config = _write_news_rss_feed_config(outside_path)
            env_file = outside_path / "data-operations.env"
            env_file.write_text(
                "\n".join(
                    [
                        'STOCKANALYSIS_PSQL_COMMAND="docker exec psql"',
                        f'STOCKANALYSIS_NEWS_RSS_FEED_CONFIG_JSON="{feed_config}"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_news_rss_configured_feeds") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "news_rss_configured_feed_run",
                    "status": "dry_run",
                    "failed_feed_count": 0,
                }
                exit_code = main(
                    [
                        "news-rss-daily-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--feed-name",
                        "free-feed",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "news_rss_configured_feed_run")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["feed_config_path"], feed_config.resolve())
            self.assertEqual(call_kwargs["feed_names"], ("free-feed",))
            self.assertTrue(call_kwargs["dry_run"])

    def test_news_rss_daily_run_rejects_repo_inside_config(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            feed_config = Path(repo_root) / "news-rss-feeds.json"
            feed_config.write_text(json.dumps(_news_rss_feed_config_payload()), encoding="utf-8")
            stderr = io.StringIO()

            exit_code = main(
                [
                    "news-rss-daily-run",
                    "--repo-root",
                    repo_root,
                    "--feed-config",
                    str(feed_config),
                    "--dry-run",
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_news_rss_enrich_run_command_passes_env_and_limit(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_news_rss_event_enrichment") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "news_rss_event_enrichment",
                    "status": "completed",
                    "failed_event_count": 0,
                }
                exit_code = main(
                    [
                        "news-rss-enrich-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--limit",
                        "7",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "news_rss_event_enrichment")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["limit"], 7)
            self.assertTrue(call_kwargs["dry_run"])

    def test_news_missing_instrument_bootstrap_run_command_passes_env_and_limits(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            company_tickers_json = Path(outside_root) / "company_tickers_exchange.json"
            company_tickers_json.write_text("{}", encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_news_missing_instrument_bootstrap") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "news_missing_instrument_bootstrap",
                    "status": "planned",
                    "run_id": None,
                    "missing_symbol_count": 1,
                    "bootstrapped_symbol_count": 0,
                }
                exit_code = main(
                    [
                        "news-missing-instrument-bootstrap-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--company-tickers-json",
                        str(company_tickers_json),
                        "--limit",
                        "12",
                        "--exchange",
                        "Nasdaq",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "news_missing_instrument_bootstrap")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["limit"], 12)
            self.assertEqual(call_kwargs["company_tickers_json_path"], str(company_tickers_json.resolve()))
            self.assertEqual(call_kwargs["exchanges"], ["Nasdaq"])
            self.assertTrue(call_kwargs["dry_run"])

    def test_news_rss_cluster_evidence_run_command_passes_env_and_limits(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_news_rss_cluster_evidence") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "news_rss_cluster_evidence",
                    "status": "planned",
                    "failed_cluster_count": 0,
                }
                exit_code = main(
                    [
                        "news-rss-cluster-evidence-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-19",
                        "--event-limit",
                        "12",
                        "--max-clusters",
                        "3",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "news_rss_cluster_evidence")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 19))
            self.assertEqual(call_kwargs["event_limit"], 12)
            self.assertEqual(call_kwargs["max_clusters"], 3)
            self.assertEqual(call_kwargs["pipeline_name"], "event_intelligence_llm_extract")
            self.assertTrue(call_kwargs["dry_run"])

    def test_news_rss_ai_extract_run_command_passes_env_and_provider_limits(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_news_rss_ai_extract") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "news_rss_ai_extract",
                    "status": "planned",
                    "failed_candidate_count": 0,
                }
                exit_code = main(
                    [
                        "news-rss-ai-extract-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-19",
                        "--limit",
                        "9",
                        "--provider",
                        "codex_oauth",
                        "--model-name",
                        "codex-cli-default",
                        "--reasoning-effort",
                        "low",
                        "--max-input-chars",
                        "2500",
                        "--min-confidence",
                        "0.75",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "news_rss_ai_extract")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 19))
            self.assertEqual(call_kwargs["limit"], 9)
            self.assertEqual(call_kwargs["provider"], "codex_oauth")
            self.assertEqual(call_kwargs["model_name"], "codex-cli-default")
            self.assertEqual(call_kwargs["reasoning_effort"], "low")
            self.assertEqual(call_kwargs["max_input_chars"], 2500)
            self.assertEqual(call_kwargs["min_confidence"], 0.75)
            self.assertFalse(call_kwargs["execute"])

    def test_news_rss_translation_run_command_passes_env_and_provider_limits(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_news_rss_translation") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "news_rss_korean_translation",
                    "status": "planned",
                    "failed_document_count": 0,
                }
                exit_code = main(
                    [
                        "news-rss-translation-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-23",
                        "--limit",
                        "7",
                        "--provider",
                        "codex_oauth",
                        "--model-name",
                        "codex-cli-default",
                        "--reasoning-effort",
                        "low",
                        "--max-input-chars",
                        "1800",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "news_rss_korean_translation")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 23))
            self.assertEqual(call_kwargs["limit"], 7)
            self.assertEqual(call_kwargs["provider"], "codex_oauth")
            self.assertEqual(call_kwargs["model_name"], "codex-cli-default")
            self.assertEqual(call_kwargs["reasoning_effort"], "low")
            self.assertEqual(call_kwargs["max_input_chars"], 1800)
            self.assertFalse(call_kwargs["execute"])

    def test_news_rss_ai_extract_run_does_not_fail_exit_on_candidate_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_news_rss_ai_extract") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "news_rss_ai_extract",
                    "status": "completed_with_fallback",
                    "failed_candidate_count": 2,
                }
                exit_code = main(
                    [
                        "news-rss-ai-extract-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--execute",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "news_rss_ai_extract")
            self.assertEqual(payload["status"], "completed_with_fallback")

    def test_macro_event_propagation_run_command_passes_env_and_execute_flag(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_macro_event_propagation") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "macro_event_propagation",
                    "status": "completed",
                    "propagated_impact_count": 3,
                }
                exit_code = main(
                    [
                        "macro-event-propagation-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-20",
                        "--limit",
                        "123",
                        "--execute",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "macro_event_propagation")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 20))
            self.assertEqual(call_kwargs["limit"], 123)
            self.assertTrue(call_kwargs["execute"])

    def test_hierarchical_impact_propagation_run_command_passes_env_and_execute_flag(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_hierarchical_impact_propagation") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "hierarchical_impact_propagation",
                    "status": "completed",
                    "propagated_impact_count": 5,
                }
                exit_code = main(
                    [
                        "hierarchical-impact-propagation-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-20",
                        "--limit",
                        "123",
                        "--max-depth",
                        "4",
                        "--decay-per-hop",
                        "0.8000",
                        "--execute",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "hierarchical_impact_propagation")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 20))
            self.assertEqual(call_kwargs["limit"], 123)
            self.assertEqual(call_kwargs["max_depth"], 4)
            self.assertEqual(call_kwargs["decay_per_hop"], Decimal("0.8000"))
            self.assertTrue(call_kwargs["execute"])

    def test_cycle_hierarchy_snapshot_v2_run_command_passes_env_and_execute_flag(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_cycle_hierarchy_snapshot_v2") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "cycle_hierarchy_snapshot_v2",
                    "status": "completed",
                    "node_count": 9,
                }
                exit_code = main(
                    [
                        "cycle-hierarchy-snapshot-v2-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-20",
                        "--execute",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "cycle_hierarchy_snapshot_v2")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 20))
            self.assertTrue(call_kwargs["execute"])

    def test_cycle_graph_context_summary_run_command_passes_env_and_execute_flag(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_cycle_graph_context_summary") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "cycle_graph_context_summary",
                    "status": "completed",
                    "node_count": 2,
                }
                exit_code = main(
                    [
                        "cycle-graph-context-summary-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-20",
                        "--node-code",
                        "MACRO_RATES_FED",
                        "--limit",
                        "9",
                        "--max-nodes",
                        "11",
                        "--execute",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "cycle_graph_context_summary")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 20))
            self.assertEqual(call_kwargs["node_codes"], ("MACRO_RATES_FED",))
            self.assertEqual(call_kwargs["limit"], 9)
            self.assertEqual(call_kwargs["max_nodes"], 11)
            self.assertTrue(call_kwargs["execute"])

    def test_cycle_community_ai_summary_v2_run_command_passes_env_provider_and_execute_flag(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_cycle_community_ai_summary_v2") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "cycle_community_ai_summary_v2",
                    "status": "completed",
                    "node_count": 1,
                }
                exit_code = main(
                    [
                        "cycle-community-ai-summary-v2-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-20",
                        "--node-code",
                        "MACRO_RATES_FED",
                        "--limit",
                        "9",
                        "--max-nodes",
                        "11",
                        "--provider",
                        "fixture",
                        "--model-name",
                        "fixture-model",
                        "--reasoning-effort",
                        "minimal",
                        "--max-context-chars",
                        "9000",
                        "--execute",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "cycle_community_ai_summary_v2")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 20))
            self.assertEqual(call_kwargs["node_codes"], ("MACRO_RATES_FED",))
            self.assertEqual(call_kwargs["limit"], 9)
            self.assertEqual(call_kwargs["max_nodes"], 11)
            self.assertEqual(call_kwargs["provider"], "fixture")
            self.assertEqual(call_kwargs["model_name"], "fixture-model")
            self.assertEqual(call_kwargs["reasoning_effort"], "minimal")
            self.assertEqual(call_kwargs["max_context_chars"], 9000)
            self.assertTrue(call_kwargs["execute"])

    def test_cycle_ai_quality_audit_run_command_passes_env_execute_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            output_path = Path(outside_root) / "cycle-ai-quality-audit.json"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_cycle_ai_quality_audit") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "cycle_ai_quality_audit",
                    "status": "completed",
                    "audit_status": "ok",
                    "issue_count": 0,
                }
                exit_code = main(
                    [
                        "cycle-ai-quality-audit-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-24",
                        "--lookback-days",
                        "21",
                        "--execute",
                        "--output",
                        str(output_path),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_name"], "cycle_ai_quality_audit")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 24))
            self.assertEqual(call_kwargs["lookback_days"], 21)
            self.assertTrue(call_kwargs["execute"])

    def test_recommendation_quality_eval_run_command_passes_env_horizon_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            output_path = Path(outside_root) / "recommendation-quality-eval.json"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_recommendation_quality_eval") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "recommendation_quality_calibration",
                    "status": "completed",
                    "horizon_days": 30,
                }
                exit_code = main(
                    [
                        "recommendation-quality-eval-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-24",
                        "--horizon",
                        "30d",
                        "--min-sample-size",
                        "7",
                        "--min-professional-coverage-rate",
                        "0.75",
                        "--execute",
                        "--output",
                        str(output_path),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_name"], "recommendation_quality_calibration")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 24))
            self.assertEqual(call_kwargs["horizon_days"], 30)
            self.assertEqual(call_kwargs["min_sample_size"], 7)
            self.assertEqual(call_kwargs["min_professional_coverage_rate"], 0.75)
            self.assertTrue(call_kwargs["execute"])

    def test_recommendation_weight_review_readiness_audit_run_command_passes_env_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            output_path = Path(outside_root) / "recommendation-weight-review-audit.json"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_recommendation_weight_review_readiness_audit") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "recommendation_weight_review_readiness_audit",
                    "status": "completed",
                    "audit": {"decision": "blocked_by_paper_validation_conflicts"},
                }
                exit_code = main(
                    [
                        "recommendation-weight-review-readiness-audit-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-25",
                        "--eval-run-id",
                        "11",
                        "--min-component-outcome-count",
                        "4",
                        "--execute",
                        "--output",
                        str(output_path),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_name"], "recommendation_weight_review_readiness_audit")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 25))
            self.assertEqual(call_kwargs["eval_run_id"], 11)
            self.assertEqual(call_kwargs["min_component_outcome_count"], 4)
            self.assertTrue(call_kwargs["execute"])

    def test_industry_competitive_positioning_run_command_passes_env_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            output_path = Path(outside_root) / "industry-competitive-positioning.json"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_industry_competitive_positioning") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "industry_competitive_positioning",
                    "status": "completed",
                    "min_metric_coverage": 4,
                }
                exit_code = main(
                    [
                        "industry-competitive-positioning-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-25",
                        "--min-metric-coverage",
                        "4",
                        "--execute",
                        "--output",
                        str(output_path),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_name"], "industry_competitive_positioning")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 25))
            self.assertEqual(call_kwargs["min_metric_coverage"], 4)
            self.assertTrue(call_kwargs["execute"])

    def test_recommendation_outcome_backfill_run_command_passes_env_filters_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            output_path = Path(outside_root) / "recommendation-outcome-backfill.json"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_recommendation_outcome_backfill") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "recommendation_outcome_backfill",
                    "status": "executed",
                    "candidate_count": 1,
                }
                exit_code = main(
                    [
                        "recommendation-outcome-backfill-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--due-on-date",
                        "2026-05-24",
                        "--horizon-day",
                        "30",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--universe-version",
                        "live-v1",
                        "--market-code",
                        "US",
                        "--outcome-version",
                        "bootstrap-v2",
                        "--limit",
                        "5",
                        "--execute",
                        "--output",
                        str(output_path),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_name"], "recommendation_outcome_backfill")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["due_on_date"], date(2026, 5, 24))
            self.assertEqual(call_kwargs["horizon_days"], (30,))
            self.assertEqual(call_kwargs["strategy_name"], "long_term_core")
            self.assertEqual(call_kwargs["horizon_type"], "long_term")
            self.assertEqual(call_kwargs["universe_version"], "live-v1")
            self.assertEqual(call_kwargs["market_code"], "US")
            self.assertEqual(call_kwargs["outcome_version"], "bootstrap-v2")
            self.assertEqual(call_kwargs["limit"], 5)
            self.assertTrue(call_kwargs["execute"])

    def test_news_ai_eval_run_command_passes_dataset_and_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            dataset_path = Path(outside_root) / "news-ai-eval.json"
            output_path = Path(outside_root) / "news-ai-eval-report.json"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            dataset_path.write_text(json.dumps({"dataset_version": "test", "cases": [{"case_id": "stub"}]}), encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_news_ai_eval") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "news_ai_eval_dataset_and_scoring",
                    "status": "completed",
                    "dataset_version": "test",
                }
                exit_code = main(
                    [
                        "news-ai-eval-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--dataset-path",
                        str(dataset_path),
                        "--model-name",
                        "fixture-model",
                        "--execute",
                        "--output",
                        str(output_path),
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), str(output_path.resolve()))
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["report_name"], "news_ai_eval_dataset_and_scoring")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["dataset_path"], dataset_path.resolve())
            self.assertEqual(call_kwargs["model_name"], "fixture-model")
            self.assertTrue(call_kwargs["execute"])

    def test_paper_validation_audit_run_command_passes_runtime_args_and_env(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_paper_validation_audit") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "paper_validation_audit_writer",
                    "status": "dry_run",
                    "validation_status": "failed",
                    "submitted_to_broker_count": 0,
                }
                exit_code = main(
                    [
                        "paper-validation-audit-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--source",
                        "live",
                        "--as-of-date",
                        "2026-05-18",
                        "--portfolio-notional",
                        "250000",
                        "--created-by",
                        "paper-validation-cli-test",
                        "--human-approved",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "paper_validation_audit_writer")
            self.assertEqual(payload["submitted_to_broker_count"], 0)
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["source"], "live")
            self.assertEqual(call_kwargs["as_of_date"].isoformat(), "2026-05-18")
            self.assertEqual(str(call_kwargs["portfolio_notional"]), "250000")
            self.assertEqual(call_kwargs["created_by"], "paper-validation-cli-test")
            self.assertTrue(call_kwargs["human_approved"])
            self.assertTrue(call_kwargs["dry_run"])

    def test_paper_validation_audit_run_rejects_repo_inside_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            env_file = Path(repo_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stderr = io.StringIO()

            exit_code = main(
                [
                    "paper-validation-audit-run",
                    "--repo-root",
                    repo_root,
                    "--env-file",
                    str(env_file),
                    "--dry-run",
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_paper_safety_bootstrap_config_command_passes_runtime_args_and_env(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_paper_safety_bootstrap_config") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "paper_safety_bootstrap_config",
                    "status": "dry_run",
                    "supports_order_submit": False,
                    "submitted_to_broker_count": 0,
                }
                exit_code = main(
                    [
                        "paper-safety-bootstrap-config",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--portfolio-name",
                        "Long Term Paper",
                        "--broker-code",
                        "simulated_paper",
                        "--account-ref",
                        "paper-account-long-term",
                        "--policy-name",
                        "long-term-paper-default",
                        "--max-single-order-notional",
                        "30000",
                        "--max-daily-order-notional",
                        "60000",
                        "--max-single-order-weight-delta",
                        "0.10",
                        "--max-post-trade-symbol-weight",
                        "0.25",
                        "--min-cash-buffer-weight",
                        "0.05",
                        "--created-by",
                        "paper-bootstrap-cli-test",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "paper_safety_bootstrap_config")
            self.assertFalse(payload["supports_order_submit"])
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertTrue(call_kwargs["dry_run"])
            bootstrap_config = call_kwargs["bootstrap_config"]
            self.assertEqual(bootstrap_config.portfolio_name, "Long Term Paper")
            self.assertEqual(bootstrap_config.broker_code, "simulated_paper")
            self.assertEqual(bootstrap_config.account_ref, "paper-account-long-term")
            self.assertEqual(str(bootstrap_config.max_single_order_notional), "30000")
            self.assertEqual(str(bootstrap_config.max_daily_order_notional), "60000")
            self.assertEqual(str(bootstrap_config.max_single_order_weight_delta), "0.10")
            self.assertEqual(str(bootstrap_config.max_post_trade_symbol_weight), "0.25")
            self.assertEqual(str(bootstrap_config.min_cash_buffer_weight), "0.05")
            self.assertEqual(bootstrap_config.created_by, "paper-bootstrap-cli-test")

    def test_paper_safety_bootstrap_config_rejects_repo_inside_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            env_file = Path(repo_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stderr = io.StringIO()

            exit_code = main(
                [
                    "paper-safety-bootstrap-config",
                    "--repo-root",
                    repo_root,
                    "--env-file",
                    str(env_file),
                    "--dry-run",
                ],
                stderr=stderr,
            )

            self.assertEqual(exit_code, 1)
            self.assertIn("outside repository", stderr.getvalue())

    def test_financial_metric_normalization_run_command_passes_env_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_financial_metric_normalization") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "financial_metric_normalization",
                    "status": "planned",
                    "recommendation_scoring_mutated": False,
                }
                exit_code = main(
                    [
                        "financial-metric-normalization-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-25",
                        "--limit",
                        "20",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "financial_metric_normalization")
            self.assertFalse(payload["recommendation_scoring_mutated"])
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 25))
            self.assertEqual(call_kwargs["limit"], 20)
            self.assertFalse(call_kwargs["execute"])

    def test_peer_relative_analysis_run_command_passes_env_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_peer_relative_analysis") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "peer_relative_analysis",
                    "status": "planned",
                    "recommendation_scoring_mutated": False,
                }
                exit_code = main(
                    [
                        "peer-relative-analysis-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-25",
                        "--statement-scope",
                        "annual",
                        "--min-peer-count",
                        "3",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "peer_relative_analysis")
            self.assertFalse(payload["recommendation_scoring_mutated"])
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 25))
            self.assertEqual(call_kwargs["statement_scope"], "annual")
            self.assertEqual(call_kwargs["min_peer_count"], 3)
            self.assertFalse(call_kwargs["execute"])

    def test_valuation_snapshot_run_command_passes_env_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_valuation_snapshot") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "valuation_snapshot",
                    "status": "planned",
                    "recommendation_scoring_mutated": False,
                }
                exit_code = main(
                    [
                        "valuation-snapshot-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-25",
                        "--statement-scope",
                        "annual",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "valuation_snapshot")
            self.assertFalse(payload["recommendation_scoring_mutated"])
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 25))
            self.assertEqual(call_kwargs["statement_scope"], "annual")
            self.assertFalse(call_kwargs["execute"])

    def test_recommendation_fundamental_components_run_command_passes_env_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_recommendation_fundamental_components") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "recommendation_fundamental_components",
                    "status": "planned",
                    "recommendation_total_score_mutated": False,
                    "recommendation_weight_mutated": False,
                }
                exit_code = main(
                    [
                        "recommendation-fundamental-components-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-25",
                        "--market-code",
                        "US",
                        "--strategy-name",
                        "long_term_core",
                        "--horizon-type",
                        "long_term",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "recommendation_fundamental_components")
            self.assertFalse(payload["recommendation_total_score_mutated"])
            self.assertFalse(payload["recommendation_weight_mutated"])
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 25))
            self.assertEqual(call_kwargs["market_code"], "US")
            self.assertEqual(call_kwargs["strategy_name"], "long_term_core")
            self.assertEqual(call_kwargs["horizon_type"], "long_term")
            self.assertFalse(call_kwargs["execute"])

    def test_equity_research_reporting_run_command_passes_env_and_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_equity_research_reporting") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "equity_research_reporting",
                    "status": "planned",
                    "recommendation_scoring_mutated": False,
                    "broker_order_submit_enabled": False,
                }
                exit_code = main(
                    [
                        "equity-research-reporting-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-25",
                        "--symbol",
                        "NVDA",
                        "--limit",
                        "1",
                        "--provider",
                        "fixture",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "equity_research_reporting")
            self.assertFalse(payload["recommendation_scoring_mutated"])
            self.assertFalse(payload["broker_order_submit_enabled"])
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 25))
            self.assertEqual(call_kwargs["symbols"], ("NVDA",))
            self.assertEqual(call_kwargs["limit"], 1)
            self.assertEqual(call_kwargs["provider"], "fixture")
            self.assertFalse(call_kwargs["execute"])

    def test_professional_coverage_expansion_run_command_passes_env_limits_and_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = Path(outside_root) / "data-operations.env"
            env_file.write_text('STOCKANALYSIS_PSQL_COMMAND="docker exec psql"\n', encoding="utf-8")
            company_tickers_json = Path(outside_root) / "company_tickers_exchange.json"
            company_tickers_json.write_text("{}", encoding="utf-8")
            stdout = io.StringIO()

            with patch("stockanalysis.operations.cli.run_professional_coverage_expansion") as runner_mock:
                runner_mock.return_value = {
                    "report_name": "professional_coverage_expansion",
                    "status": "planned",
                    "candidate_symbol_count": 0,
                }
                exit_code = main(
                    [
                        "professional-coverage-expansion-run",
                        "--repo-root",
                        repo_root,
                        "--env-file",
                        str(env_file),
                        "--as-of-date",
                        "2026-05-25",
                        "--limit",
                        "12",
                        "--companyfacts-limit",
                        "4",
                        "--research-limit",
                        "3",
                        "--research-provider",
                        "fixture",
                        "--company-tickers-json",
                        str(company_tickers_json),
                        "--exchange",
                        "Nasdaq",
                        "--dry-run",
                    ],
                    stdout=stdout,
                )

            self.assertEqual(exit_code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["report_name"], "professional_coverage_expansion")
            call_kwargs = runner_mock.call_args.kwargs
            self.assertEqual(call_kwargs["config"].psql_command, "docker exec psql")
            self.assertEqual(call_kwargs["as_of_date"], date(2026, 5, 25))
            self.assertEqual(call_kwargs["limit"], 12)
            self.assertEqual(call_kwargs["companyfacts_limit"], 4)
            self.assertEqual(call_kwargs["research_limit"], 3)
            self.assertEqual(call_kwargs["research_provider"], "fixture")
            self.assertEqual(call_kwargs["company_tickers_json_path"], str(company_tickers_json.resolve()))
            self.assertEqual(call_kwargs["exchanges"], ["Nasdaq"])
            self.assertFalse(call_kwargs["execute"])


class DataOperationsEnvFileTests(unittest.TestCase):
    def test_load_env_file_values_supports_quotes_export_and_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_file = Path(tmp_dir) / "data-operations.env"
            env_file.write_text(
                "\n".join(
                    [
                        "# comment",
                        'STOCKANALYSIS_SEC_USER_AGENT="stockanalysis test@example.com"',
                        "export STOCKANALYSIS_LLM_PROVIDER=openai",
                    ]
                ),
                encoding="utf-8",
            )

            values = load_env_file_values(env_file)

            self.assertEqual(values["STOCKANALYSIS_SEC_USER_AGENT"], "stockanalysis test@example.com")
            self.assertEqual(values["STOCKANALYSIS_LLM_PROVIDER"], "openai")


class DataOperationsPathPolicyTests(unittest.TestCase):
    def test_resolve_existing_file_can_require_repo_outside(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            outside_file = Path(outside_root) / "report.json"
            outside_file.write_text("{}", encoding="utf-8")

            resolved = resolve_existing_file(
                outside_file,
                label="report",
                repo_root=repo_root,
                require_repo_outside=True,
            )

            self.assertEqual(resolved, outside_file.resolve())

    def test_resolve_output_path_rejects_repo_inside_output(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root:
            with self.assertRaisesRegex(ValueError, "outside repository"):
                resolve_output_path(
                    Path(repo_root) / "output.json",
                    label="output",
                    repo_root=repo_root,
                    require_repo_outside=True,
                )


def _execution_request_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_host_activation_execution_request",
        "execution_request": "pending_explicit_execution_approval",
        "requested_user_decision_values": [
            "approve_host_activation_execution",
            "deny_host_activation_execution",
        ],
        "requires_explicit_execution_approval": True,
        "execution_allowed_by_plan": True,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_allowed_in_this_task": False,
        "job_id": "macro-weekly",
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "execution_command_preview": [
            'install -m 600 "/tmp/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
        "rollback_command_preview": [
            'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
        "manual_next_step": "data-operations-live-scheduler-host-activation-execution-decision",
    }


def _host_activation_execution_report() -> dict[str, object]:
    return {
        "report_name": "data_operations_live_scheduler_host_activation_execution",
        "execution_gate": "confirmed_for_manual_host_mutation_not_executed_by_this_task",
        "host_activation_execution_allowed_in_this_task": False,
        "host_activation_execution_allowed_for_manual_operator": True,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_performed": False,
        "job_id": "macro-weekly",
        "pipeline_name": "Macro Weekly",
        "domain": "macro",
        "cadence": "weekly",
        "rendered_label": "com.stockanalysis.data-operations.macro-weekly",
        "host_plist_path_preview": "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist",
        "execution_command_preview": [
            'install -m 600 "/tmp/rendered.plist" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
            'launchctl bootstrap "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
        "rollback_command_preview": [
            'launchctl bootout "gui/$(id -u)" "~/Library/LaunchAgents/com.stockanalysis.data-operations.macro-weekly.plist"',
        ],
        "manual_next_step": "manual-host-scheduler-activation",
    }


def _manual_approval_report() -> dict[str, object]:
    host_report = _host_activation_execution_report()
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
        "job_id": host_report["job_id"],
        "pipeline_name": host_report["pipeline_name"],
        "domain": host_report["domain"],
        "cadence": host_report["cadence"],
        "rendered_label": host_report["rendered_label"],
        "host_plist_path_preview": host_report["host_plist_path_preview"],
        "exact_execution_commands": host_report["execution_command_preview"],
        "exact_rollback_commands": host_report["rollback_command_preview"],
        "manual_next_step": "manual-host-scheduler-activation-operator-evidence",
    }


def _write_runtime_env_file(root: Path) -> Path:
    positions_csv = root / "positions.csv"
    positions_csv.write_text("symbol,quantity\nAAPL,1\n", encoding="utf-8")
    market_watchlist_csv = root / "market-watchlist.csv"
    market_watchlist_csv.write_text("symbol\nAAPL\n", encoding="utf-8")
    artifact_root = root / "artifacts"
    feed_config = _write_news_rss_feed_config(root)
    env_file = root / "data-operations.env"
    env_file.write_text(
        "\n".join(
            [
                'STOCKANALYSIS_DATABASE_URL="postgresql://stockanalysis:stockanalysis@localhost:5432/stockanalysis"',
                'STOCKANALYSIS_FRED_API_KEY="fred-key-12345"',
                'STOCKANALYSIS_MARKET_PRICE_PROVIDER="twelve_data"',
                'STOCKANALYSIS_TWELVE_DATA_API_KEY="twelve-key-12345"',
                f'STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV="{market_watchlist_csv}"',
                f'STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH="{root / "market-ledger.json"}"',
                'STOCKANALYSIS_ALPHA_VANTAGE_API_KEY="alpha-key-12345"',
                'STOCKANALYSIS_SEC_USER_AGENT="stockanalysis ops@stock.local"',
                f'STOCKANALYSIS_NEWS_RSS_FEED_CONFIG_JSON="{feed_config}"',
                f'STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV="{positions_csv}"',
                'STOCKANALYSIS_LLM_PROVIDER="openai"',
                'OPENAI_API_KEY="openai-key-12345"',
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return env_file


def _write_news_rss_feed_config(root: Path) -> Path:
    feed_config = root / "news-rss-feeds.json"
    feed_config.write_text(json.dumps(_news_rss_feed_config_payload()), encoding="utf-8")
    return feed_config


def _news_rss_feed_config_payload() -> dict[str, object]:
    return {
        "version": "news-rss-feed-config-v1",
        "feeds": [
            {
                "feed_name": "free-feed",
                "feed_url": "https://example.com/free/rss",
                "enabled": True,
                "limit": 25,
                "default_language": "en",
            }
        ],
    }


if __name__ == "__main__":
    unittest.main()
