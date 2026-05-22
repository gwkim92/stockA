from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from stockanalysis.operations.operating_data_profile_scheduler import (
    build_operating_data_profile_scheduler_invocation_plan,
    build_operating_data_profile_scheduler_status_report,
    render_operating_data_profile_scheduler_invocation_markdown,
)


class OperatingDataProfileSchedulerTests(unittest.TestCase):
    def test_default_profiles_are_profile_split_and_secret_free(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = _write_runtime_env(Path(outside_root))

            report = build_operating_data_profile_scheduler_invocation_plan(
                scheduler_target="cron",
                repo_root=repo_root,
                runtime_root=Path(outside_root) / "runtime",
                data_operations_env_file=env_file,
                profile_output_root=Path(outside_root) / "reports",
                timeout_seconds=777,
                python_executable="/usr/bin/python3",
                generated_at=datetime(2026, 5, 20, tzinfo=timezone.utc),
            )

        self.assertEqual(report["report_name"], "operating_data_profile_scheduler_invocation_boundary")
        self.assertEqual(report["scheduler_target"], "cron")
        self.assertFalse(report["include_full_recovery"])
        self.assertEqual(report["total_profile_count"], 7)
        profile_ids = [profile["profile_id"] for profile in report["profiles"]]
        self.assertEqual(profile_ids[0], "market-universe-weekly")
        self.assertEqual(profile_ids[1], "sec-filings-weekly")
        self.assertNotIn("full-recovery", profile_ids)
        self.assertEqual(report["schedules"][0]["schedule"], "0 7 * * 1")
        self.assertNotIn("hidden-profile-pass", json.dumps(report))
        self.assertNotIn("postgresql://", json.dumps(report))

    def test_full_recovery_requires_explicit_schedule(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = _write_runtime_env(Path(outside_root))

            with self.assertRaises(ValueError):
                build_operating_data_profile_scheduler_invocation_plan(
                    scheduler_target="cron",
                    repo_root=repo_root,
                    runtime_root=Path(outside_root) / "runtime",
                    data_operations_env_file=env_file,
                    include_full_recovery=True,
                )

            report = build_operating_data_profile_scheduler_invocation_plan(
                scheduler_target="cron",
                repo_root=repo_root,
                runtime_root=Path(outside_root) / "runtime",
                data_operations_env_file=env_file,
                include_full_recovery=True,
                schedule="30 18 * * 1-5",
                profile_ids=("full-recovery",),
            )

        self.assertTrue(report["include_full_recovery"])
        self.assertEqual(len(report["profiles"]), 1)
        self.assertEqual(report["profiles"][0]["profile_id"], "full-recovery")
        self.assertEqual(report["profiles"][0]["schedule"], "30 18 * * 1-5")
        self.assertEqual(report["schedules"][0]["schedule"], "30 18 * * 1-5")

    def test_manifest_output_root_writes_manifest_files(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = _write_runtime_env(Path(outside_root))
            manifest_root = Path(outside_root) / "manifests"

            report = build_operating_data_profile_scheduler_invocation_plan(
                scheduler_target="systemd",
                repo_root=repo_root,
                runtime_root=Path(outside_root) / "runtime",
                data_operations_env_file=env_file,
                manifest_output_root=manifest_root,
                profile_ids=("news-intraday",),
                schedule="0 6 * * 1-5",
                execute=True,
            )

            self.assertTrue(manifest_root.is_dir())
            self.assertEqual(report["manifest_output_root"], str(manifest_root.resolve()))
            self.assertEqual(len(report["manifest_records"]), 1)
            manifest_record = dict(report["manifest_records"][0])
            manifest = dict(manifest_record["manifest"])
            self.assertEqual(manifest_record["profile_id"], "news-intraday")
            self.assertEqual(manifest["target"], "systemd")
            self.assertTrue(manifest["operating_data_run_execute"])
            self.assertIn("--execute", manifest["command_argv"])
            self.assertIn("kind", manifest)
            self.assertEqual(len(report["profiles"][0]["manifest_file_previews"]), 3)
            for item in report["profiles"][0]["manifest_file_previews"]:
                self.assertIn("path", item)
                path = Path(item["path"])
                self.assertTrue(path.is_file(), f"missing manifest file: {path}")
                self.assertNotIn("hidden-profile-pass", path.read_text(encoding="utf-8"))
                if item["kind"] == "systemd_timer":
                    self.assertIn("OnCalendar=Mon..Fri *-*-* 06:00 America/New_York", path.read_text(encoding="utf-8"))

    def test_systemd_manifest_can_pin_runtime_user_and_home(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = _write_runtime_env(Path(outside_root))
            manifest_root = Path(outside_root) / "manifests"

            report = build_operating_data_profile_scheduler_invocation_plan(
                scheduler_target="systemd",
                repo_root=repo_root,
                runtime_root=Path(outside_root) / "runtime",
                data_operations_env_file=env_file,
                manifest_output_root=manifest_root,
                profile_ids=("news-intraday",),
                schedule="0 6 * * 1-5",
                execute=True,
                systemd_user="ec2-user",
                systemd_group="ec2-user",
                systemd_home="/home/ec2-user",
            )

            self.assertEqual(report["systemd_user"], "ec2-user")
            self.assertEqual(report["systemd_group"], "ec2-user")
            self.assertEqual(report["systemd_home"], "/home/ec2-user")
            service_paths = [
                Path(item["path"])
                for item in report["profiles"][0]["manifest_file_previews"]
                if item["kind"] == "systemd_service"
            ]
            self.assertEqual(len(service_paths), 1)
            service_text = service_paths[0].read_text(encoding="utf-8")
            self.assertIn("User=ec2-user\n", service_text)
            self.assertIn("Group=ec2-user\n", service_text)
            self.assertIn("Environment=HOME=/home/ec2-user\n", service_text)
            self.assertIn("Environment=CODEX_HOME=/home/ec2-user/.codex\n", service_text)
            self.assertIn("Environment=XDG_CONFIG_HOME=/home/ec2-user/.config\n", service_text)
            preview = report["profiles"][0]["target_manifest_preview"]
            self.assertEqual(preview["run_user"], "ec2-user")
            self.assertEqual(preview["run_home"], "/home/ec2-user")

    def test_systemd_user_options_require_systemd_target(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            with self.assertRaises(ValueError):
                build_operating_data_profile_scheduler_invocation_plan(
                    scheduler_target="cron",
                    repo_root=repo_root,
                    runtime_root=Path(outside_root) / "runtime",
                    data_operations_env_file=_write_runtime_env(Path(outside_root)),
                    profile_ids=("news-intraday",),
                    systemd_user="ec2-user",
                )

    def test_systemd_target_rejects_unsupported_schedule_pattern(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            env_file = _write_runtime_env(Path(outside_root))

            with self.assertRaises(ValueError):
                build_operating_data_profile_scheduler_invocation_plan(
                    scheduler_target="systemd",
                    repo_root=repo_root,
                    runtime_root=Path(outside_root) / "runtime",
                    data_operations_env_file=env_file,
                    profile_ids=("news-intraday",),
                    schedule="*/x 9-18 * * 1-5",
                )

    def test_systemd_target_converts_default_profile_schedules(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            manifest_root = Path(outside_root) / "manifests"

            report = build_operating_data_profile_scheduler_invocation_plan(
                scheduler_target="systemd",
                repo_root=repo_root,
                runtime_root=Path(outside_root) / "runtime",
                data_operations_env_file=_write_runtime_env(Path(outside_root)),
                manifest_output_root=manifest_root,
                python_executable="/usr/bin/python3",
            )

            self.assertEqual(report["total_profile_count"], 7)
            calendars = {}
            for profile in report["profiles"]:
                profile_payload = dict(profile)
                for item in profile_payload["manifest_file_previews"]:
                    if item["kind"] == "systemd_timer":
                        calendars[profile_payload["profile_id"]] = Path(item["path"]).read_text(encoding="utf-8")
            self.assertIn("OnCalendar=Mon *-*-* 07:00 America/New_York", calendars["market-universe-weekly"])
            self.assertIn("OnCalendar=Mon *-*-* 08:00 America/New_York", calendars["sec-filings-weekly"])
            self.assertIn("OnCalendar=Mon..Fri *-*-* 09..18:00/30 America/New_York", calendars["news-intraday"])
            self.assertIn("OnCalendar=Mon..Fri *-*-* 18:35 America/New_York", calendars["market-daily"])
            self.assertIn("OnCalendar=Mon..Fri *-*-* 19:00 America/New_York", calendars["decision-daily"])
            self.assertIn("OnCalendar=Mon *-*-* 07:30 America/New_York", calendars["macro-weekly"])
            self.assertIn("OnCalendar=*-*-01 09:30 America/New_York", calendars["performance-monthly"])

    def test_markdown_renderer_keeps_boundary_visible(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            report = build_operating_data_profile_scheduler_invocation_plan(
                scheduler_target="systemd",
                repo_root=repo_root,
                runtime_root=Path(outside_root) / "runtime",
                data_operations_env_file=_write_runtime_env(Path(outside_root)),
                profile_ids=("news-intraday", "market-daily"),
                schedule="0 1 * * 1",
            )

            markdown = render_operating_data_profile_scheduler_invocation_markdown(report)

            self.assertIn("Operating Data Profile Scheduler Invocation Boundary", markdown)
            self.assertIn("schedule", markdown)
            self.assertIn("news-intraday", markdown)
            self.assertIn("does not deploy any scheduler", markdown)

    def test_status_report_reads_profile_timer_state(self) -> None:
        def fake_runner(argv):
            command = tuple(argv)
            if command[:2] == ("systemctl", "is-active"):
                return "active"
            if command[:3] == ("systemctl", "show", "stockanalysis-operating-data-news-intraday.timer"):
                return "Thu 2026-05-21 13:00:00 UTC"
            if command[:3] == ("systemctl", "show", "stockanalysis-operating-data-news-intraday.service"):
                return "success"
            return ""

        report = build_operating_data_profile_scheduler_status_report(
            profile_ids=("news-intraday",),
            generated_at=datetime(2026, 5, 21, tzinfo=timezone.utc),
            command_runner=fake_runner,
        )

        self.assertEqual(report["report_name"], "operating_data_profile_scheduler_status")
        self.assertEqual(report["install_status"], "installed")
        self.assertEqual(report["timer_count"], 1)
        self.assertEqual(report["active_timer_count"], 1)
        self.assertEqual(report["timers"][0]["profile_id"], "news-intraday")
        self.assertEqual(report["timers"][0]["active_state"], "active")
        self.assertNotIn("postgresql://", json.dumps(report))


def _write_runtime_env(root: Path) -> Path:
    env_file = root / "data-operations.env"
    env_file.write_text(
        "STOCKANALYSIS_DATABASE_URL=\"postgresql://user:hidden-profile-pass@localhost/db\"\\n"
        + "STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT=\"/tmp/artifacts\"\\n",
        encoding="utf-8",
    )
    return env_file


if __name__ == "__main__":
    unittest.main()
