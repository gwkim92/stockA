from __future__ import annotations

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from stockanalysis.operations.artifact_runner import run_data_operation_artifact_command
from stockanalysis.operations.batch_runtime import (
    BatchProgress, atomic_json, observe_profile, public_observation, run_profile_with_progress,
)
from stockanalysis.operations.operating_data_profile_scheduler import build_operating_data_profile_scheduler_status_report


def process_running(pid):
    result = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True)
    return bool(result.stdout.strip()) and not result.stdout.strip().startswith("Z")


class BatchProcessTests(unittest.TestCase):
    def run_command(self, root, code, **kwargs):
        return run_data_operation_artifact_command(job_id="macro-weekly", artifact_root=root,
            command_argv=[sys.executable, "-c", code], **kwargs)

    @unittest.skipUnless(os.name == "posix", "POSIX process groups")
    def test_timeout_kills_descendant_even_when_it_ignores_term(self):
        with tempfile.TemporaryDirectory() as root:
            child_code = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)"
            code = f"import subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c',{child_code!r}]); print(p.pid,flush=True); time.sleep(60)"
            before = time.monotonic()
            result = self.run_command(root, code, timeout_seconds=1)
            pid = int(Path(result["stdout_path"]).read_text().strip())
            self.assertEqual(result["status"], "timeout")
            self.assertEqual(result["exit_code"], 124)
            self.assertLess(time.monotonic() - before, 5)
            for _ in range(20):
                if not process_running(pid):
                    break
                time.sleep(.05)
            self.assertFalse(process_running(pid))
            self.assertEqual(json.loads((Path(result["artifact_dir"]) / "progress.json").read_text())["status"], "timeout")

    def test_output_limit_is_bounded_on_disk_and_reported_as_failure(self):
        with tempfile.TemporaryDirectory() as root, patch("stockanalysis.operations.artifact_runner.MAX_OUTPUT_BYTES", 1024):
            result = self.run_command(root, "print('x'*10000)")
            self.assertEqual(result["status"], "output_limit")
            self.assertEqual(result["exit_code"], 125)
            self.assertEqual(Path(result["stdout_path"]).stat().st_size, 1024)

    def test_silent_valid_work_does_not_trigger_timeout(self):
        with tempfile.TemporaryDirectory() as root:
            result = self.run_command(root, "import time; time.sleep(.15); print('{}')", timeout_seconds=1)
            self.assertEqual(result["status"], "succeeded")

    def test_spawn_failure_is_persisted(self):
        with tempfile.TemporaryDirectory() as root:
            result = run_data_operation_artifact_command(job_id="macro-weekly", artifact_root=root,
                                                        command_argv=[root + "/missing-executable"])
            self.assertEqual(result["exit_code"], 127)
            self.assertEqual(json.loads(Path(result["metadata_path"]).read_text())["status"], "failed")

    @unittest.skipUnless(os.name == "posix", "POSIX signals")
    def test_runner_sigterm_cleans_child_and_saves_interruption(self):
        with tempfile.TemporaryDirectory() as root:
            child_pid = Path(root) / "child.pid"
            code = f"import os,time,pathlib; pathlib.Path({str(child_pid)!r}).write_text(str(os.getpid())); time.sleep(60)"
            wrapper = ("import json,sys; from stockanalysis.operations.artifact_runner import run_data_operation_artifact_command; "
                       f"r=run_data_operation_artifact_command(job_id='macro-weekly',artifact_root={root!r},command_argv=[sys.executable,'-c',{code!r}]); print(json.dumps(r))")
            process = subprocess.Popen([sys.executable, "-c", wrapper], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                for _ in range(100):
                    if child_pid.exists():
                        break
                    time.sleep(.02)
                self.assertTrue(child_pid.exists())
                running_file = next(Path(root).glob("*/progress.json"))
                self.assertEqual(json.loads(running_file.read_text())["status"], "running")
                process.send_signal(signal.SIGTERM)
                stdout, stderr = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 0, stderr)
                self.assertEqual(json.loads(stdout)["status"], "interrupted")
                self.assertFalse(process_running(int(child_pid.read_text())))
            finally:
                if process.poll() is None:
                    process.kill()
                process.communicate(timeout=5)


class BatchObservationTests(unittest.TestCase):
    props = ("LoadState=loaded\nActiveState=activating\nResult=success\nSlice=stockanalysis-batch.slice\n"
             "MemoryMax=1073741824\nTimeoutStartUSec=15min\nInactiveExitTimestampMonotonic=100000000\n")

    def observe(self, root, payload, **kwargs):
        path = Path(root) / "progress.json"
        atomic_json(path, payload)
        return observe_profile(kwargs.pop("props", self.props), path, now=kwargs.pop("now", 200), current_boot_id="boot", **kwargs)

    def payload(self, **kwargs):
        return {"boot_id": "boot", "started_monotonic": 101, "step_started_monotonic": 110,
                "timeout_seconds": 100, "completed_steps": 1, "step_id": "financial-refresh", "status": "running", **kwargs}

    def test_running_then_stalled_by_step_deadline(self):
        with tempfile.TemporaryDirectory() as root:
            running = self.observe(root, self.payload())
            self.assertEqual(running["status"], "running")
            self.assertTrue(running["resource_limits_applied"])
            stalled = self.observe(root, self.payload(), now=250)
            self.assertEqual(stalled["status"], "stalled")
            self.assertTrue(stalled["attention_required"])

    def test_old_boot_or_old_run_is_not_current_progress(self):
        with tempfile.TemporaryDirectory() as root:
            for payload in (self.payload(boot_id="previous"), self.payload(started_monotonic=50)):
                self.assertEqual(self.observe(root, payload, now=150)["status"], "awaiting_progress")
                self.assertEqual(self.observe(root, payload, now=250)["status"], "progress_missing")

    def test_inactive_running_marker_means_interrupted(self):
        with tempfile.TemporaryDirectory() as root:
            props = self.props.replace("ActiveState=activating", "ActiveState=inactive")
            self.assertEqual(self.observe(root, self.payload(), props=props)["status"], "interrupted")
            self.assertEqual(self.observe(root, self.payload(status="succeeded"), props=props)["status"], "succeeded")
            self.assertEqual(self.observe(root, self.payload(), props=props.replace("Result=success", "Result=timeout"))["status"], "unit_failed")

    def test_corrupt_progress_and_unprotected_unit_do_not_pass(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertEqual(self.observe(root, {"timeout_seconds": "secret"})["status"], "invalid_progress")
            result = self.observe(root, self.payload(), props=self.props.replace("MemoryMax=1073741824", "MemoryMax=infinity"))
            self.assertFalse(result["resource_limits_applied"])

    def test_public_observation_drops_unexpected_secret_fields(self):
        result = public_observation({"status": "running", "token": "secret-value", "memory_max_bytes": "bad", "attention_required": "false"})
        self.assertNotIn("secret-value", json.dumps(result))
        self.assertIsNone(result["memory_max_bytes"])
        self.assertFalse(result["attention_required"])
        self.assertEqual(public_observation({"status": []})["status"], "invalid_progress")

    def test_profile_progress_records_stage_count_and_interruption(self):
        with tempfile.TemporaryDirectory() as repo, tempfile.TemporaryDirectory() as runtime:
            def run(**kwargs):
                progress = kwargs["_progress"]
                progress.step("one")
                progress.completed_step()
                raise RuntimeError("do not persist sensitive error")
            with self.assertRaises(RuntimeError):
                run_profile_with_progress(run, repo_root=repo, runtime_root=runtime, profile="research-maintenance", execute=True, timeout_seconds=100)
            text = (Path(runtime) / "batch-progress/research-maintenance.json").read_text()
            self.assertEqual(json.loads(text)["status"], "interrupted")
            self.assertEqual(json.loads(text)["completed_steps"], 1)
            self.assertNotIn("sensitive", text)

    def test_scheduler_aggregates_limits_and_stalled_work(self):
        def command(argv):
            if argv[0] == "docker":
                return "3221225472 3221225472"
            if argv[1] == "is-active":
                return "active"
            if argv[2] == "stockanalysis-batch.slice":
                return "MemoryMax=2147483648\nCPUQuotaPerSecUSec=1s"
            if argv[-1].startswith("--property="):
                return self.props
            return "loaded" if "LoadState" in argv else "success"
        with tempfile.TemporaryDirectory() as root, patch("stockanalysis.operations.batch_runtime.time.monotonic", return_value=300), patch("stockanalysis.operations.batch_runtime.boot_id", return_value="boot"):
            atomic_json(Path(root) / "batch-progress/research-maintenance.json", self.payload())
            report = build_operating_data_profile_scheduler_status_report(
                profile_ids=["research-maintenance"], runtime_root=root, command_runner=command)
            self.assertEqual(report["batch_runtime"]["status"], "protected")
            self.assertEqual(report["batch_runtime"]["attention_profile_count"], 1)
            self.assertTrue(report["batch_runtime"]["database_limits_applied"])
            self.assertEqual(report["timers"][0]["runtime_guard"]["status"], "stalled")
            drift = build_operating_data_profile_scheduler_status_report(profile_ids=["research-maintenance"],
                runtime_root=root, command_runner=lambda argv: "0 0" if argv[0] == "docker" else command(argv))
            self.assertEqual(drift["batch_runtime"]["status"], "unprotected")
            self.assertFalse(drift["batch_runtime"]["database_limits_applied"])

    def test_api_guard_filters_private_fields_and_marks_old_report_stale(self):
        from stockanalysis.frontend.live_adapter import _load_operating_data_profile_scheduler_status_for_data_health
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "report.json"
            payload = {"report_name": "operating_data_profile_scheduler_status", "generated_at": datetime.now(timezone.utc).isoformat(),
                "timers": [{"runtime_guard": {"status": "running", "token": "never-expose", "completed_steps": 2}}],
                "batch_runtime": {"status": "protected", "monitored_profile_count": 1, "protected_profile_count": 1,
                    "attention_profile_count": 0, "shared_limits_applied": True, "environment": "never-expose"}}
            atomic_json(path, payload)
            with patch.dict(os.environ, {"STOCKANALYSIS_OPERATING_DATA_PROFILE_SCHEDULER_STATUS_REPORT": str(path)}):
                report = _load_operating_data_profile_scheduler_status_for_data_health()
                self.assertEqual(report["batch_runtime"]["status"], "protected")
                self.assertEqual(report["timers"][0]["runtime_guard"]["completed_steps"], 2)
                self.assertNotIn("never-expose", json.dumps(report))
                payload["generated_at"] = "2001-01-01T00:00:00Z"
                atomic_json(path, payload)
                self.assertEqual(_load_operating_data_profile_scheduler_status_for_data_health()["batch_runtime"]["status"], "stale")
