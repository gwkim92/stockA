from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from stockanalysis.operations.artifact_runner import (
    run_data_operation_artifact_command,
)


class DataOperationsArtifactRunnerTests(unittest.TestCase):
    def test_runner_captures_stdout_stderr_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_data_operation_artifact_command(
                job_id="macro-weekly",
                artifact_root=tmpdir,
                command_argv=[
                    sys.executable,
                    "-c",
                    "import json, sys; print(json.dumps({'ok': True})); print('warn', file=sys.stderr)",
                ],
                started_at=datetime(2026, 5, 3, 0, 0, tzinfo=timezone.utc),
                completed_at=datetime(2026, 5, 3, 0, 0, 1, tzinfo=timezone.utc),
            )

            artifact_dir = Path(str(result["artifact_dir"]))
            self.assertEqual(result["status"], "succeeded")
            self.assertEqual(result["exit_code"], 0)
            self.assertEqual(result["duration_ms"], 1000)
            self.assertTrue((artifact_dir / "stdout.txt").exists())
            self.assertTrue((artifact_dir / "stdout.json").exists())
            self.assertTrue((artifact_dir / "stderr.log").exists())
            self.assertTrue((artifact_dir / "metadata.json").exists())
            self.assertEqual(json.loads((artifact_dir / "stdout.json").read_text(encoding="utf-8")), {"ok": True})
            self.assertIn("warn", (artifact_dir / "stderr.log").read_text(encoding="utf-8"))

    def test_runner_captures_failed_exit_without_raising(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_data_operation_artifact_command(
                job_id="macro-weekly",
                artifact_root=tmpdir,
                command_argv=[sys.executable, "-c", "import sys; print('bad'); sys.exit(7)"],
            )

            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["exit_code"], 7)
            self.assertTrue(Path(str(result["stdout_path"])).exists())

    def test_runner_redacts_sensitive_command_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_data_operation_artifact_command(
                job_id="macro-weekly",
                artifact_root=tmpdir,
                command_argv=[
                    sys.executable,
                    "-c",
                    "print('{}')",
                    "--api-key",
                    "plain-secret",
                    "DATABASE_URL=postgresql://user:password@example/db",
                    "postgresql://user:password@example/db",
                ],
            )

            metadata = json.loads(Path(str(result["metadata_path"])).read_text(encoding="utf-8"))
            metadata_text = json.dumps(metadata)
            self.assertIn("[REDACTED]", metadata_text)
            self.assertNotIn("plain-secret", metadata_text)
            self.assertNotIn("user:password", metadata_text)

    def test_runner_requires_known_job_and_artifact_root(self) -> None:
        with self.assertRaises(ValueError):
            run_data_operation_artifact_command(
                job_id="unknown-job",
                artifact_root="/tmp/stockanalysis-unused",
                command_argv=[sys.executable, "-c", "print('{}')"],
            )

        with self.assertRaises(ValueError):
            run_data_operation_artifact_command(
                job_id="macro-weekly",
                env={},
                command_argv=[sys.executable, "-c", "print('{}')"],
            )


if __name__ == "__main__":
    unittest.main()
