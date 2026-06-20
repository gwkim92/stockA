from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stockanalysis.frontend.codex_oauth_operator import (
    CommandResult,
    STATUS_PATH_ENV,
    load_codex_oauth_operator_status,
    run_codex_oauth_direct_smoke,
    run_codex_oauth_news_smoke,
)


class CodexOauthOperatorTests(unittest.TestCase):
    def test_missing_status_artifact_reports_unknown_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "status.json"
            with patch.dict("os.environ", {STATUS_PATH_ENV: str(status_path)}, clear=False):
                status = load_codex_oauth_operator_status(repo_root=tmpdir)

        self.assertEqual(status["status"], "unknown")
        self.assertEqual(status["label"], "미확인")
        self.assertTrue(status["admin_action_required"])
        self.assertEqual(status["order_boundary"], "read_only_no_order")
        self.assertFalse(status["broker_submit_allowed"])
        self.assertNotIn("token", json.dumps(status).lower())

    def test_direct_smoke_success_marks_oauth_healthy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "status.json"

            def runner(command, input_text, timeout_seconds, cwd):
                self.assertIn("--sandbox", command)
                self.assertIn("read-only", command)
                self.assertIn("--ignore-user-config", command)
                self.assertIn("--ignore-rules", command)
                self.assertEqual(cwd, Path(tmpdir).resolve())
                return CommandResult(returncode=0, stdout='{"status":"ok"}', stderr="")

            with patch.dict("os.environ", {STATUS_PATH_ENV: str(status_path)}, clear=False):
                status = run_codex_oauth_direct_smoke(repo_root=tmpdir, runner=runner)

        self.assertEqual(status["status"], "healthy")
        self.assertEqual(status["label"], "정상")
        self.assertEqual(status["last_smoke_status"], "succeeded")
        self.assertEqual(status["order_boundary"], "read_only_no_order")

    def test_direct_smoke_auth_failure_requires_relogin(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "status.json"

            def runner(command, input_text, timeout_seconds, cwd):
                return CommandResult(returncode=1, stdout="", stderr="401 Unauthorized: refresh_token_invalidated")

            with patch.dict("os.environ", {STATUS_PATH_ENV: str(status_path)}, clear=False):
                status = run_codex_oauth_direct_smoke(repo_root=tmpdir, runner=runner)

        self.assertEqual(status["status"], "relogin_required")
        self.assertEqual(status["last_error_code"], "codex_oauth_auth_invalid")
        self.assertIn("401", status["last_error_summary"])

    def test_news_smoke_requires_repo_outside_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "status.json"
            with patch.dict(
                "os.environ",
                {
                    STATUS_PATH_ENV: str(status_path),
                    "STOCKANALYSIS_CODEX_OAUTH_SMOKE_ENV_FILE": "",
                    "STOCKANALYSIS_DATA_OPERATIONS_ENV_FILE": "",
                },
                clear=False,
            ):
                status = run_codex_oauth_news_smoke(repo_root=tmpdir)

        self.assertEqual(status["status"], "failed")
        self.assertEqual(status["last_error_code"], "missing_env_file")
        self.assertIn("env_file", status["last_error_code"])


if __name__ == "__main__":
    unittest.main()
