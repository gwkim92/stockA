from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from stockanalysis.operations.alert_destination import (
    AlertHttpResult,
    build_alert_destination_test_report,
)
from stockanalysis.operations.cli import main as operations_cli_main


class AlertDestinationFreeChannelTests(unittest.TestCase):
    def test_dry_run_reports_target_without_sending_or_leaking_url(self) -> None:
        report = build_alert_destination_test_report(
            env={
                "STOCKANALYSIS_ALERT_DESTINATION_MODE": "webhook",
                "STOCKANALYSIS_ALERT_DESTINATION_TYPE": "ntfy",
                "STOCKANALYSIS_NTFY_TOPIC_URL": "https://ntfy.sh/private-topic-token",
            },
            execute=False,
            now=datetime(2026, 5, 27, tzinfo=timezone.utc),
        )

        serialized = json.dumps(report)
        self.assertEqual(report["status"], "dry_run_not_sent")
        self.assertEqual(report["last_test_status"], "not_executed")
        self.assertEqual(report["destination_type"], "ntfy")
        self.assertEqual(report["target_host"], "ntfy.sh")
        self.assertNotIn("private-topic-token", serialized)
        self.assertNotIn("https://ntfy.sh", serialized)

    def test_execute_posts_ntfy_message_and_writes_passed_status(self) -> None:
        calls: list[tuple[str, bytes, dict[str, str], float]] = []

        def fake_post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> AlertHttpResult:
            calls.append((url, body, headers, timeout))
            return AlertHttpResult(status_code=200, response_header_count=2)

        report = build_alert_destination_test_report(
            env={"STOCKANALYSIS_NTFY_TOPIC_URL": "https://ntfy.sh/private-topic-token"},
            destination_type="ntfy",
            mode="webhook",
            execute=True,
            now=datetime(2026, 5, 27, tzinfo=timezone.utc),
            title="테스트",
            message="도달 테스트",
            http_post=fake_post,
        )

        self.assertEqual(report["last_test_status"], "passed")
        self.assertEqual(report["last_tested_at"], "2026-05-27T00:00:00Z")
        self.assertEqual(report["http_status_class"], "2xx")
        self.assertEqual(calls[0][1], "도달 테스트".encode("utf-8"))
        self.assertEqual(calls[0][2]["Title"], "테스트")

    def test_execute_missing_target_fails_without_secret_output(self) -> None:
        report = build_alert_destination_test_report(
            env={},
            destination_type="ntfy",
            execute=True,
            now=datetime(2026, 5, 27, tzinfo=timezone.utc),
        )

        self.assertEqual(report["status"], "missing_target")
        self.assertEqual(report["last_test_status"], "failed")
        self.assertFalse(report["target_configured"])

    def test_cli_writes_status_artifact_to_repo_outside_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = Path(tmpdir) / "alert.env"
            output_path = Path(tmpdir) / "alert-status.json"
            env_path.write_text(
                "\n".join(
                    [
                        "STOCKANALYSIS_ALERT_DESTINATION_MODE=webhook",
                        "STOCKANALYSIS_ALERT_DESTINATION_TYPE=ntfy",
                        "STOCKANALYSIS_NTFY_TOPIC_URL=https://ntfy.sh/private-topic-token",
                        f"STOCKANALYSIS_ALERT_DESTINATION_STATUS_PATH={output_path}",
                    ]
                ),
                encoding="utf-8",
            )

            status = operations_cli_main(
                [
                    "alert-destination-test-run",
                    "--env-file",
                    str(env_path),
                    "--repo-root",
                    str(Path.cwd()),
                ]
            )

            self.assertEqual(status, 0)
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["last_test_status"], "not_executed")
            self.assertEqual(payload["destination_type"], "ntfy")
            self.assertNotIn("private-topic-token", json.dumps(payload))


if __name__ == "__main__":
    unittest.main()
