from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from stockanalysis.operations.operating_data_profile_scheduler import (
    build_operating_data_profile_scheduler_invocation_plan,
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
        self.assertEqual(report["total_profile_count"], 5)
        profile_ids = [profile["profile_id"] for profile in report["profiles"]]
        self.assertNotIn("full-recovery", profile_ids)
        self.assertEqual(report["schedules"][0]["schedule"], "*/30 9-18 * * 1-5")
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

            self.assertEqual(report["total_profile_count"], 5)
            calendars = {}
            for profile in report["profiles"]:
                profile_payload = dict(profile)
                for item in profile_payload["manifest_file_previews"]:
                    if item["kind"] == "systemd_timer":
                        calendars[profile_payload["profile_id"]] = Path(item["path"]).read_text(encoding="utf-8")
            self.assertIn("OnCalendar=Mon..Fri *-*-* 09..18:00/30 America/New_York", calendars["news-intraday"])
            self.assertIn("OnCalendar=Mon..Fri *-*-* 18:35 America/New_York", calendars["market-daily"])
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
