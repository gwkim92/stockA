from __future__ import annotations

import shlex
from pathlib import Path
from typing import Sequence

from stockanalysis.operations.artifact_runner import redact_command_argv
from stockanalysis.operations.cadence import get_data_operation_cadence


LAUNCHD_WEEKDAYS = {
    "Sunday": 1,
    "Monday": 2,
    "Tuesday": 3,
    "Wednesday": 4,
    "Thursday": 5,
    "Friday": 6,
    "Saturday": 7,
}


def default_launchd_label(job_id: str) -> str:
    safe_job_id = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in job_id).strip("-")
    if not safe_job_id:
        raise ValueError("job_id must include at least one safe label character.")
    return f"com.stockanalysis.data-operations.{safe_job_id}"


def build_data_operations_launchd_plist(
    *,
    job_id: str,
    repo_root: str | Path,
    env_file: str | Path,
    wrapper_path: str | Path,
    output_dir: str | Path,
    command_argv: Sequence[str],
    label: str | None = None,
    timeout_seconds: int = 3600,
) -> dict[str, object]:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive.")
    command = tuple(str(part) for part in command_argv)
    if not command:
        raise ValueError("scheduler install dry-run command must not be empty.")
    _reject_sensitive_command_argv(command)

    job = get_data_operation_cadence(job_id)
    label_value = label or default_launchd_label(job.job_id)
    output_path = Path(output_dir)
    launchd_command = _render_launchd_shell_command(
        wrapper_path=Path(wrapper_path),
        env_file=Path(env_file),
        job_id=job.job_id,
        timeout_seconds=timeout_seconds,
        command_argv=command,
    )

    return {
        "Label": label_value,
        "ProgramArguments": ["/bin/bash", "-lc", launchd_command],
        "WorkingDirectory": str(Path(repo_root)),
        "StartCalendarInterval": _launchd_schedule_for_job(job_id=job.job_id),
        "StandardOutPath": str(output_path / f"{label_value}.stdout.log"),
        "StandardErrorPath": str(output_path / f"{label_value}.stderr.log"),
        "RunAtLoad": False,
    }


def build_data_operations_scheduler_install_manifest(
    *,
    job_id: str,
    label: str,
    plist_path: str | Path,
    env_file: str | Path,
    wrapper_path: str | Path,
    output_dir: str | Path,
    command_argv: Sequence[str],
    timeout_seconds: int,
) -> dict[str, object]:
    job = get_data_operation_cadence(job_id)
    _reject_sensitive_command_argv(tuple(str(part) for part in command_argv))
    return {
        "report_name": "data_operations_scheduler_install_dry_run",
        "install_mode": "dry_run",
        "scheduler_type": "launchd",
        "scheduler_activation": "not_installed",
        "job_id": job.job_id,
        "pipeline_name": job.pipeline_name,
        "domain": job.domain,
        "cadence": job.cadence,
        "label": label,
        "plist_path": str(Path(plist_path)),
        "output_dir": str(Path(output_dir)),
        "env_file": str(Path(env_file)),
        "wrapper_path": str(Path(wrapper_path)),
        "timeout_seconds": timeout_seconds,
        "command_argv": list(command_argv),
        "schedule": _launchd_schedule_for_job(job_id=job.job_id),
        "host_install_path_written": False,
        "secrets_policy": "env_file_path_only_no_env_values",
    }


def _reject_sensitive_command_argv(command_argv: Sequence[str]) -> None:
    redacted = redact_command_argv(command_argv)
    if list(command_argv) != redacted:
        raise ValueError("scheduler install dry-run command argv contains sensitive values; move secrets to the env file.")


def _render_launchd_shell_command(
    *,
    wrapper_path: Path,
    env_file: Path,
    job_id: str,
    timeout_seconds: int,
    command_argv: Sequence[str],
) -> str:
    parts = [
        "exec",
        "/bin/bash",
        str(wrapper_path),
        "--env-file",
        str(env_file),
        "--job-id",
        job_id,
        "--timeout-seconds",
        str(timeout_seconds),
        "--",
        *command_argv,
    ]
    return " ".join(shlex.quote(part) for part in parts)


def _launchd_schedule_for_job(*, job_id: str) -> list[dict[str, int]]:
    job = get_data_operation_cadence(job_id)
    if job.cadence == "monthly":
        raise ValueError("Monthly first-business-day data operations need a separate calendar-aware scheduler strategy.")

    parts = job.expected_after_local.split()
    hour, minute = _parse_time(parts[0])
    if job.cadence == "intraday":
        end_hour = 17
        return [
            {"Weekday": weekday, "Hour": scheduled_hour, "Minute": minute}
            for weekday in range(2, 7)
            for scheduled_hour in range(hour, end_hour + 1)
        ]
    if job.cadence == "daily":
        return [{"Weekday": weekday, "Hour": hour, "Minute": minute} for weekday in range(2, 7)]
    if job.cadence == "weekly":
        if len(parts) != 2:
            raise ValueError(f"Weekly job {job.job_id!r} expected_after_local must include weekday.")
        try:
            weekday = LAUNCHD_WEEKDAYS[parts[1]]
        except KeyError as exc:
            raise ValueError(f"Unsupported weekly launchd weekday: {parts[1]!r}.") from exc
        return [{"Weekday": weekday, "Hour": hour, "Minute": minute}]
    raise ValueError(f"Unsupported cadence for launchd dry-run: {job.cadence!r}.")


def _parse_time(value: str) -> tuple[int, int]:
    try:
        hour_raw, minute_raw = value.split(":", 1)
        hour = int(hour_raw)
        minute = int(minute_raw)
    except ValueError as exc:
        raise ValueError(f"Invalid expected_after_local time: {value!r}.") from exc
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(f"Invalid launchd time: {value!r}.")
    return hour, minute
