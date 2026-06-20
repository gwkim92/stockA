from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from stockanalysis.frontend.codex_oauth_operator import (
    CommandResult,
    STATUS_PATH_ENV,
    _extract_auth_url,
    _extract_user_code,
    load_codex_oauth_operator_status,
    run_codex_oauth_direct_smoke,
    run_codex_oauth_news_smoke,
)


class CodexOauthOperatorTests(unittest.TestCase):
    def _status_runner(self, stdout: str, returncode: int = 0):
        def runner(command, input_text, timeout_seconds, cwd):
            self.assertEqual(command[-2:], ["login", "status"])
            return CommandResult(returncode=returncode, stdout=stdout, stderr="")

        return runner

    def test_device_auth_parser_ignores_ansi_and_command_line_text(self) -> None:
        output = (
            "\x1b[90mOpenAI's command-line coding agent\x1b[0m\n"
            "Open this link \x1b[94mhttps://auth.openai.com/codex/device\x1b[0m\n"
            "Enter this one-time code \x1b[94mX1FR-GKMLX\x1b[0m\n"
        )

        self.assertEqual(_extract_auth_url(output), "https://auth.openai.com/codex/device")
        self.assertEqual(_extract_user_code(output), "X1FR-GKMLX")

    def test_missing_status_artifact_reports_unknown_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "status.json"
            with patch.dict("os.environ", {STATUS_PATH_ENV: str(status_path)}, clear=False):
                status = load_codex_oauth_operator_status(
                    repo_root=tmpdir,
                    status_runner=self._status_runner("Not logged in", returncode=1),
                )

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
        self.assertEqual(status["last_error_summary"], "")
        self.assertEqual(status["order_boundary"], "read_only_no_order")

    def test_pending_device_auth_is_not_rendered_as_recent_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "status.json"
            status_path.write_text(
                json.dumps(
                    {
                        "updated_at": "2026-06-20T05:00:00Z",
                        "events": [
                            {
                                "event_type": "device_auth_started",
                                "status": "device_auth_pending",
                                "auth_url": "https://auth.openai.com/codex/device",
                                "user_code": "X1LP-L0QP3",
                                "expires_at": "2099-06-20T06:00:00Z",
                                "output_excerpt": "Enter this one-time code X1LP-L0QP3",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict("os.environ", {STATUS_PATH_ENV: str(status_path)}, clear=False):
                status = load_codex_oauth_operator_status(
                    repo_root=tmpdir,
                    status_runner=self._status_runner("Not logged in", returncode=1),
                )

        self.assertEqual(status["status"], "device_auth_pending")
        self.assertEqual(status["last_error_summary"], "")
        self.assertEqual(status["user_code"], "X1LP-L0QP3")

    def test_completed_device_auth_is_detected_by_codex_login_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            status_path = Path(tmpdir) / "status.json"
            status_path.write_text(
                json.dumps(
                    {
                        "updated_at": "2026-06-20T05:00:00Z",
                        "events": [
                            {
                                "event_type": "device_auth_started",
                                "status": "device_auth_pending",
                                "auth_url": "https://auth.openai.com/codex/device",
                                "user_code": "X1LP-L0QP3",
                                "expires_at": "2099-06-20T06:00:00Z",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict("os.environ", {STATUS_PATH_ENV: str(status_path)}, clear=False):
                status = load_codex_oauth_operator_status(
                    repo_root=tmpdir,
                    status_runner=self._status_runner("Logged in using ChatGPT"),
                )

        self.assertEqual(status["status"], "authenticated_smoke_required")
        self.assertEqual(status["label"], "로그인 확인됨")
        self.assertEqual(status["auth_url"], "")
        self.assertEqual(status["user_code"], "")
        self.assertEqual(status["login_probe_status"], "logged_in")

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
