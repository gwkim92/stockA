from __future__ import annotations

import json
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence

from stockanalysis.operations.operating_data_orchestrator import (
    OPERATING_DATA_RUN_PROFILE_IDS,
    OPERATING_DATA_RUN_PROFILES,
)
from stockanalysis.operations.cadence import DATA_OPERATIONS_TIMEZONE
from stockanalysis.operations.server_scheduler_invocation import SERVER_SCHEDULER_TARGETS
from stockanalysis.operations.path_policy import (
    ensure_repo_outside,
    resolve_existing_file,
    resolve_output_path,
    resolve_repo_root,
)
from stockanalysis.operations.local_runtime_status import DEFAULT_LOCAL_RUNTIME_ROOT
from stockanalysis.operations.artifact_runner import redact_command_argv


DEFAULT_PROFILE_SCHEDULER_JOB_NAME = "stockanalysis-operating-data"
DEFAULT_PROFILE_CADENCE_SCHEDULES = {
    "intraday": "*/30 9-18 * * 1-5",
    "daily": "35 18 * * 1-5",
    "weekly": "30 7 * * 1",
    "monthly": "30 9 1 * *",
}
DEFAULT_PROFILE_SCHEDULES = {
    "market-universe-weekly": "0 7 * * 1",
    "sec-filings-weekly": "0 8 * * 1",
    "news-intraday": "0 0,2,4,6,8,10,12,14,16,18,20,22 * * *",
    "market-daily": "35 18 * * 1-5",
    "decision-daily": "0 19 * * 1-5",
    "macro-weekly": "30 7 * * 1",
    "performance-monthly": "30 9 1 * *",
}
PROFILE_OUTPUT_ROOT_DEFAULT_SEGMENT = "operating-data-profile-scheduler-reports"
PROFILE_SCHEDULER_MANIFEST_ROOT_DEFAULT_SEGMENT = "operating-data-profile-scheduler-manifests"
FORBIDDEN_PROFILE_SCHEDULER_TOKENS = (
    "postgresql://",
    "api-key=",
    "api_key=",
    "bearer ",
    "password=",
    "sk-",
)
SystemCommandRunner = Callable[[Sequence[str]], str]


def build_operating_data_profile_scheduler_invocation_plan(
    *,
    scheduler_target: str,
    repo_root: str | Path | None = None,
    runtime_root: str | Path = DEFAULT_LOCAL_RUNTIME_ROOT,
    data_operations_env_file: str | Path,
    profile_output_root: str | Path | None = None,
    profile_ids: Sequence[str] | None = None,
    include_full_recovery: bool = False,
    manifest_output_root: str | Path | None = None,
    schedule: str | None = None,
    timeout_seconds: int = 3600,
    python_executable: str | Path | None = None,
    execute: bool = False,
    job_name: str = DEFAULT_PROFILE_SCHEDULER_JOB_NAME,
    systemd_user: str | None = None,
    systemd_group: str | None = None,
    systemd_home: str | Path | None = None,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    target = _normalize_target(scheduler_target)
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive.")
    normalized_schedule = str(schedule).strip() if schedule is not None else None
    if normalized_schedule is not None and not normalized_schedule:
        raise ValueError("schedule must not be empty.")
    if not str(job_name).strip():
        raise ValueError("job_name must not be empty.")
    normalized_systemd_user = _normalize_optional_systemd_token(systemd_user, label="systemd user")
    normalized_systemd_group = _normalize_optional_systemd_token(systemd_group, label="systemd group")
    normalized_systemd_home = _normalize_optional_systemd_home(systemd_home)
    if target != "systemd" and any((normalized_systemd_user, normalized_systemd_group, normalized_systemd_home)):
        raise ValueError("systemd user/group/home options require --target systemd.")

    repo_root_path = resolve_repo_root(repo_root)
    runtime_root_path = ensure_repo_outside(
        Path(runtime_root).expanduser().resolve(),
        repo_root=repo_root_path,
        label="operating data runtime root",
    )
    env_file_path = resolve_existing_file(
        data_operations_env_file,
        label="operating data profile scheduler data operations env file",
        repo_root=repo_root_path,
        require_repo_outside=True,
    )
    profile_output_root_path = resolve_output_path(
        profile_output_root
        if profile_output_root is not None
        else (runtime_root_path / PROFILE_OUTPUT_ROOT_DEFAULT_SEGMENT),
        label="operating data profile scheduler output root",
        repo_root=repo_root_path,
        require_repo_outside=True,
    )
    if profile_output_root_path.exists() and not profile_output_root_path.is_dir():
        raise ValueError("profile-output-root must resolve to a directory path.")
    profile_output_root_path.mkdir(parents=True, exist_ok=True)

    manifest_output_root_path = (
        ensure_repo_outside(
            Path(manifest_output_root).expanduser().resolve(),
            repo_root=repo_root_path,
            label="operating data profile scheduler manifest output root",
        )
        if manifest_output_root is not None
        else None
    )
    if manifest_output_root_path is not None:
        manifest_output_root_path.mkdir(parents=True, exist_ok=True)

    selected_profiles = _select_profiles(profile_ids=profile_ids, include_full_recovery=include_full_recovery)
    include_full_recovery = any(profile["profile_id"] == "full-recovery" for profile in selected_profiles)
    if include_full_recovery and normalized_schedule is None:
        raise ValueError("full-recovery scheduling requires an explicit --schedule.")
    profiles_payload: list[dict[str, object]] = []
    manifest_records: list[dict[str, object]] = []
    for profile in selected_profiles:
        profile_job_name = f"{str(job_name).strip()}-{profile['profile_id']}"
        profile_schedule = (
            normalized_schedule
            if normalized_schedule is not None
            else DEFAULT_PROFILE_SCHEDULES.get(
                profile["profile_id"],
                DEFAULT_PROFILE_CADENCE_SCHEDULES.get(profile["cadence"]),
            )
        )
        if profile_schedule is None:
            raise ValueError(f"missing default schedule for cadence: {profile['cadence']}")
        if target == "systemd":
            _cron_schedule_to_systemd_calendar(profile_schedule)
        command = _build_operating_data_run_command_argv(
            repo_root=repo_root_path,
            runtime_root=runtime_root_path,
            data_operations_env_file=env_file_path,
            profile_id=profile["profile_id"],
            timeout_seconds=timeout_seconds,
            python_executable=python_executable,
            execute=execute,
            output_path=profile_output_root_path / f"{profile['profile_id']}-operating-data-run.json",
        )
        shell_command = _shell_command(repo_root=repo_root_path, command_argv=command)
        manifest_payload = _build_profile_scheduler_manifest_payload(
            target=target,
            profile_id=profile["profile_id"],
            job_name=profile_job_name,
            schedule=profile_schedule,
            shell_command=shell_command,
            command_argv=command,
            repo_root=repo_root_path,
            env_file_path=env_file_path,
            execute=execute,
            systemd_user=normalized_systemd_user,
            systemd_group=normalized_systemd_group,
            systemd_home=normalized_systemd_home,
        )
        manifest_output_paths: list[dict[str, str]] = []
        if manifest_output_root_path is not None:
            manifest_output_paths = _write_profile_scheduler_manifests(
                manifest_root=manifest_output_root_path,
                profile_id=profile["profile_id"],
                manifest_payload=manifest_payload,
            )
        profiles_payload.append(
            {
                "profile_id": profile["profile_id"],
                "label": profile["label"],
                "cadence": profile["cadence"],
                "schedule": profile_schedule,
                "recommended_schedule": profile["recommended_schedule"],
                "command_argv_preview": list(redact_command_argv(command)),
                "shell_command_preview": shell_command,
                "target_manifest_preview": _target_manifest_preview(
                    target=target,
                    job_name=profile_job_name,
                    schedule=profile_schedule,
                    command_argv=command,
                    shell_command=shell_command,
                    repo_root=repo_root_path,
                    env_file_path=env_file_path,
                    profile_id=profile["profile_id"],
                    systemd_user=normalized_systemd_user,
                    systemd_group=normalized_systemd_group,
                    systemd_home=normalized_systemd_home,
                ),
                "manifest_file_previews": manifest_output_paths,
            }
        )
        manifest_records.append(
            {
                "profile_id": profile["profile_id"],
                "manifest": manifest_payload,
            }
        )

    report: dict[str, object] = {
        "report_name": "operating_data_profile_scheduler_invocation_boundary",
        "generated_at": _format_timestamp(generated_at or datetime.now(timezone.utc)),
        "scheduler_target": target,
        "scheduler_job_name": str(job_name).strip(),
        "systemd_user": normalized_systemd_user or "",
        "systemd_group": normalized_systemd_group or "",
        "systemd_home": normalized_systemd_home or "",
        "runtime_root": str(runtime_root_path),
        "repo_root": str(repo_root_path),
        "data_operations_env_file": str(env_file_path),
        "profile_output_root": str(profile_output_root_path),
        "include_full_recovery": include_full_recovery,
        "timeout_seconds": timeout_seconds,
        "scheduler_mutation_blocked": True,
        "child_command_executed": False,
        "schedules": [
            {
                "profile_id": profile["profile_id"],
                "schedule": (
                    normalized_schedule
                    if normalized_schedule is not None
                    else DEFAULT_PROFILE_SCHEDULES.get(
                        profile["profile_id"],
                        DEFAULT_PROFILE_CADENCE_SCHEDULES[profile["cadence"]],
                    )
                ),
            }
            for profile in selected_profiles
        ],
        "manifest_output_root": str(manifest_output_root_path) if manifest_output_root_path is not None else "",
        "operating_data_run_execute": execute,
        "manifest_records": manifest_records,
        "profiles": profiles_payload,
        "total_profile_count": len(profiles_payload),
        "secrets_policy": "command_previews_and_paths_only_no_env_values",
        "manual_next_step": "server-scheduler-deployment-target-decision",
    }
    _assert_secret_free(report)
    return report


def render_operating_data_profile_scheduler_invocation_markdown(report: Mapping[str, object]) -> str:
    _assert_secret_free(report)
    manifest_output_root = str(report.get("manifest_output_root", "")).strip()
    manifest_records = report.get("manifest_records")
    manifest_record_count = len(manifest_records) if isinstance(manifest_records, list) else 0
    lines = [
        "# Operating Data Profile Scheduler Invocation Boundary",
        "",
        f"- target: `{report.get('scheduler_target', '')}`",
        f"- scheduler mutating: `{str(report.get('scheduler_mutation_blocked')).lower()}`",
        f"- profile output root: `{report.get('profile_output_root', '')}`",
        f"- manifest output root: `{manifest_output_root}`",
        f"- manifest count: `{manifest_record_count}`",
        "",
        "## Profile Invocations",
        "",
    ]
    profiles = report.get("profiles", [])
    for profile in profiles:
        profile_payload = dict(profile)
        if not isinstance(profile_payload, Mapping):
            continue
        lines.extend(
            [
                f"### {profile_payload.get('profile_id', '')}",
                f"- schedule: `{profile_payload.get('schedule', '')}`",
                f"- cadence: `{profile_payload.get('cadence', '')}`",
                f"- shell command:",
                "",
                "```bash",
                f"{profile_payload.get('shell_command_preview', '')}",
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "- This report only renders invocation packets; it does not deploy any scheduler.",
            "- It must not write host state, execute child commands, or mutate secret values.",
            "- Child commands write data only when this report is rendered with operating-data-run execute mode.",
        ]
    )
    return "\n".join(lines)


def build_operating_data_profile_scheduler_status_report(
    *,
    profile_ids: Sequence[str] | None = None,
    job_name: str = DEFAULT_PROFILE_SCHEDULER_JOB_NAME,
    generated_at: datetime | None = None,
    command_runner: SystemCommandRunner | None = None,
) -> dict[str, object]:
    if not str(job_name).strip():
        raise ValueError("job_name must not be empty.")
    selected_profiles = _select_profiles(profile_ids=profile_ids, include_full_recovery=False)
    command = command_runner or _run_system_command_text
    timers: list[dict[str, object]] = []
    for profile in selected_profiles:
        profile_id = str(profile["profile_id"])
        profile_job_name = f"{str(job_name).strip()}-{profile_id}"
        timer_name = f"{profile_job_name}.timer"
        service_name = f"{profile_job_name}.service"
        schedule = DEFAULT_PROFILE_SCHEDULES.get(
            profile_id,
            DEFAULT_PROFILE_CADENCE_SCHEDULES[profile["cadence"]],
        )
        timers.append(
            {
                "profile_id": profile_id,
                "timer_name": timer_name,
                "service_name": service_name,
                "schedule": _cron_schedule_to_systemd_calendar(schedule)[0],
                "active_state": command(("systemctl", "is-active", timer_name)) or "unknown",
                "next_elapse": command(("systemctl", "show", timer_name, "-p", "NextElapseUSecRealtime", "--value")),
                "last_result": command(("systemctl", "show", service_name, "-p", "Result", "--value")),
            }
        )

    active_timer_count = sum(1 for timer in timers if timer["active_state"] == "active")
    timer_count = len(timers)
    install_status = (
        "installed"
        if timer_count > 0 and active_timer_count == timer_count
        else "partial"
        if active_timer_count > 0
        else "not_installed"
    )
    report: dict[str, object] = {
        "report_name": "operating_data_profile_scheduler_status",
        "generated_at": _format_timestamp(generated_at or datetime.now(timezone.utc)),
        "status": install_status,
        "install_status": install_status,
        "scheduler_type": "systemd",
        "scheduler_job_name": str(job_name).strip(),
        "timer_count": timer_count,
        "active_timer_count": active_timer_count,
        "timers": timers,
        "secrets_policy": "systemd_unit_names_and_status_only_no_env_values",
    }
    _assert_secret_free(report)
    return report


def _build_profile_scheduler_manifest_payload(
    *,
    target: str,
    profile_id: str,
    job_name: str,
    schedule: str,
    shell_command: str,
    command_argv: Sequence[str],
    repo_root: Path,
    env_file_path: Path,
    execute: bool,
    systemd_user: str | None = None,
    systemd_group: str | None = None,
    systemd_home: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "kind": "operating_data_profile_scheduler_manifest",
        "target": target,
        "profile_id": str(profile_id),
        "operating_data_run_execute": bool(execute),
        "job_name": str(job_name),
        "schedule": str(schedule).strip(),
        "generated_at": _format_timestamp(datetime.now(timezone.utc)),
        "repo_root": str(repo_root),
        "data_operations_env_file": str(env_file_path),
        "shell_command": shell_command,
        "command_argv": [str(arg) for arg in command_argv],
        "target_manifest_preview": _target_manifest_preview(
            target=target,
            job_name=str(job_name),
            schedule=str(schedule),
            command_argv=command_argv,
            shell_command=shell_command,
            repo_root=repo_root,
            env_file_path=env_file_path,
            profile_id=str(profile_id),
            systemd_user=systemd_user,
            systemd_group=systemd_group,
            systemd_home=systemd_home,
        ),
        "secrets_policy": "manifest_paths_and_redacted_references_only",
    }
    if target == "systemd":
        payload["systemd_user"] = systemd_user or ""
        payload["systemd_group"] = systemd_group or ""
        payload["systemd_home"] = systemd_home or ""
    return payload


def _build_profile_scheduler_manifest_files(
    *,
    target: str,
    profile_id: str,
    job_name: str,
    schedule: str,
    shell_command: str,
    command_argv: Sequence[str],
    repo_root: Path,
    env_file_path: Path,
    systemd_user: str | None = None,
    systemd_group: str | None = None,
    systemd_home: str | None = None,
) -> list[tuple[str, str, str]]:
    safe_job_name = _safe_manifest_token(job_name)
    safe_profile_id = _safe_manifest_token(profile_id)
    files: list[tuple[str, str, str]] = []

    if target == "cron":
        files.append(
            (
                f"{safe_job_name}.cron",
                "cron",
                f"{schedule} cd {shlex.quote(str(repo_root))} && {shell_command}\n",
            )
        )
        return files

    if target == "systemd":
        systemd_calendar, conversion_note = _cron_schedule_to_systemd_calendar(schedule)
        timer_note = f"\n# conversion_note={conversion_note}" if conversion_note else ""
        escaped_command = shell_command.replace('"', '\\"')
        service_identity = _systemd_service_identity_lines(
            systemd_user=systemd_user,
            systemd_group=systemd_group,
            systemd_home=systemd_home,
        )
        files.append(
            (
                f"{safe_job_name}.service",
                "systemd_service",
                (
                    "[Unit]\n"
                    f"Description=stockanalysis operating-data-profile schedule for {safe_profile_id}\n"
                    "After=network-online.target\n"
                    "\n"
                    "[Service]\n"
                    "Type=oneshot\n"
                    f"{service_identity}"
                    f"WorkingDirectory={repo_root}\n"
                    f"EnvironmentFile={env_file_path}\n"
                    'ExecStart=/bin/bash -lc "'
                    + escaped_command
                    + '"\n'
                    "Restart=no\n"
                ),
            )
        )
        files.append(
            (
                f"{safe_job_name}.timer",
                "systemd_timer",
                (
                    "[Unit]\n"
                    f"Description=stockanalysis operating-data-profile schedule timer for {safe_profile_id}\n"
                    "Requires=network-online.target\n"
                    "\n"
                    "[Timer]\n"
                    f"OnCalendar={systemd_calendar}\n"
                    f"{timer_note}\n"
                    "Persistent=true\n"
                    "\n"
                    "[Install]\n"
                    "WantedBy=timers.target\n"
                ),
            )
        )
        return files

    if target == "kubernetes_cronjob":
        files.append(
            (
                f"{safe_job_name}.kubernetes-cronjob.json",
                "kubernetes_cronjob",
                json.dumps(
                    {
                        "kind": "kubernetes_cronjob_profile_plan",
                        "metadata": {
                            "name": safe_job_name,
                        },
                        "spec": {
                            "schedule": schedule,
                            "command_argv": list(redact_command_argv(command_argv)),
                            "shell_command": shell_command,
                            "runtime": {
                                "repo_root": str(repo_root),
                                "environment_file": str(env_file_path),
                            },
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
            )
        )
        return files

    if target == "managed_scheduler":
        files.append(
            (
                f"{safe_job_name}.managed-scheduler.json",
                "managed_scheduler",
                json.dumps(
                    {
                        "kind": "managed_scheduler_profile_plan",
                        "job_name": job_name,
                        "profile_id": str(profile_id),
                        "schedule": schedule,
                        "command_argv": list(redact_command_argv(command_argv)),
                        "shell_command": shell_command,
                        "runtime": {
                            "repo_root": str(repo_root),
                            "environment_file": str(env_file_path),
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
            )
        )
        return files

    raise ValueError(f"unsupported scheduler target: {target}")


def _write_profile_scheduler_manifests(
    *,
    manifest_root: Path,
    profile_id: str,
    manifest_payload: Mapping[str, object],
) -> list[dict[str, str]]:
    if not manifest_root.is_dir():
        raise ValueError("manifest output root must resolve to a directory.")
    profile_id_value = str(profile_id)
    safe_job_name = _safe_manifest_token(str(manifest_payload.get("job_name", "")).strip() or f"{profile_id_value}")
    manifest_target = str(manifest_payload.get("target", "")).strip()
    command_argv = manifest_payload.get("command_argv", ())
    if not isinstance(command_argv, Sequence):
        raise ValueError("manifest payload command_argv must be a sequence.")

    manifest_files = _build_profile_scheduler_manifest_files(
        target=manifest_target,
        profile_id=profile_id_value,
        job_name=safe_job_name,
        schedule=str(manifest_payload.get("schedule", "")),
        shell_command=str(manifest_payload.get("shell_command", "")),
        command_argv=tuple(str(item) for item in command_argv),
        repo_root=Path(str(manifest_payload.get("repo_root", ""))),
        env_file_path=Path(str(manifest_payload.get("data_operations_env_file", ""))),
        systemd_user=str(manifest_payload.get("systemd_user") or "") or None,
        systemd_group=str(manifest_payload.get("systemd_group") or "") or None,
        systemd_home=str(manifest_payload.get("systemd_home") or "") or None,
    )
    rendered: list[dict[str, str]] = []
    for filename, kind, contents in manifest_files:
        output_path = manifest_root / filename
        output_path.write_text(contents, encoding="utf-8")
        rendered.append({"kind": kind, "path": str(output_path)})

    manifest_json_path = manifest_root / f"{safe_job_name}.manifest.json"
    manifest_json_path.write_text(
        json.dumps(manifest_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    rendered.append({"kind": "manifest_record", "path": str(manifest_json_path)})
    return rendered


def _safe_manifest_token(value: str) -> str:
    safe = "".join(
        char if char.isalnum() or char in {"-", "_", "."} else "-" for char in str(value).strip()
    )
    safe = safe.strip("-_ .")
    return safe or "manifest"


def _normalize_optional_systemd_token(value: str | None, *, label: str) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    if any(char.isspace() for char in normalized) or any(char in normalized for char in ('"', "'", "\\")):
        raise ValueError(f"{label} must be a plain system account token.")
    if any(ord(char) < 32 for char in normalized):
        raise ValueError(f"{label} must not contain control characters.")
    return normalized


def _normalize_optional_systemd_home(value: str | Path | None) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if not normalized:
        return None
    if not normalized.startswith("/"):
        raise ValueError("systemd home must be an absolute path.")
    if any(char.isspace() for char in normalized) or any(char in normalized for char in ('"', "'", "\\")):
        raise ValueError("systemd home must not contain whitespace or quotes.")
    if any(ord(char) < 32 for char in normalized):
        raise ValueError("systemd home must not contain control characters.")
    return normalized.rstrip("/") or "/"


def _systemd_service_identity_lines(
    *,
    systemd_user: str | None,
    systemd_group: str | None,
    systemd_home: str | None,
) -> str:
    lines: list[str] = []
    if systemd_user:
        lines.append(f"User={systemd_user}")
    if systemd_group:
        lines.append(f"Group={systemd_group}")
    if systemd_home:
        lines.append(f"Environment=HOME={systemd_home}")
        lines.append(f"Environment=CODEX_HOME={systemd_home}/.codex")
        lines.append(f"Environment=XDG_CONFIG_HOME={systemd_home}/.config")
    return "".join(f"{line}\n" for line in lines)


def _cron_schedule_to_systemd_calendar(value: str) -> tuple[str, str]:
    parts = str(value).split()
    if len(parts) != 5:
        raise ValueError("unsupported cron format for systemd; expected 'minute hour * * weekday'.")

    minute_part, hour_part, day_of_month, month, dow = parts
    if month != "*":
        raise ValueError("systemd conversion supports only wildcard month fields.")

    date_part = _cron_date_to_systemd_date(day_of_month)
    time_part = _cron_time_to_systemd_time(hour_part=hour_part, minute_part=minute_part)
    if dow in ("*", ""):
        weekday_prefix = ""
    else:
        try:
            if "-" in dow and dow.count("-") == 1:
                weekday_prefix = _cron_dow_range_to_systemd_weekday(dow)
            elif "," in dow:
                weekday_prefix = ",".join(_cron_dow_single_to_systemd_weekday(value=item) for item in dow.split(","))
            else:
                weekday_prefix = _cron_dow_single_to_systemd_weekday(value=dow)
        except ValueError:
            raise

    prefix = f"{weekday_prefix} " if weekday_prefix else ""
    return f"{prefix}{date_part} {time_part} {DATA_OPERATIONS_TIMEZONE}", ""


def _cron_date_to_systemd_date(day_of_month: str) -> str:
    if day_of_month == "*":
        return "*-*-*"
    try:
        day = int(day_of_month)
    except ValueError:
        raise ValueError("systemd conversion requires numeric day-of-month or wildcard.")
    if not (1 <= day <= 31):
        raise ValueError("systemd conversion requires day-of-month in 1-31.")
    return f"*-*-{day:02d}"


def _cron_time_to_systemd_time(*, hour_part: str, minute_part: str) -> str:
    hours = _cron_hour_to_systemd_hour(hour_part)
    if minute_part.startswith("*/"):
        step_text = minute_part[2:]
        try:
            step = int(step_text)
        except ValueError:
            raise ValueError("systemd conversion requires numeric minute step.")
        if not (1 <= step <= 59):
            raise ValueError("systemd conversion requires minute step in 1-59.")
        return f"{hours}:00/{step}"
    try:
        minute = int(minute_part)
    except ValueError:
        raise ValueError("systemd conversion requires numeric minute or minute step.")
    if not (0 <= minute <= 59):
        raise ValueError("systemd conversion requires minute in 0-59.")
    return f"{hours}:{minute:02d}"


def _cron_hour_to_systemd_hour(hour_part: str) -> str:
    if "-" in hour_part and hour_part.count("-") == 1:
        start_text, end_text = hour_part.split("-", 1)
        start = _parse_cron_hour(start_text)
        end = _parse_cron_hour(end_text)
        if start > end:
            raise ValueError("systemd conversion requires ascending hour range.")
        return f"{start:02d}..{end:02d}"
    if "," in hour_part:
        return ",".join(f"{_parse_cron_hour(part):02d}" for part in hour_part.split(","))
    return f"{_parse_cron_hour(hour_part):02d}"


def _parse_cron_hour(value: str) -> int:
    try:
        hour = int(str(value).strip())
    except ValueError:
        raise ValueError("systemd conversion requires numeric hour tokens.")
    if not (0 <= hour <= 23):
        raise ValueError("systemd conversion requires hour in 0-23.")
    return hour


def _cron_dow_single_to_systemd_weekday(value: str) -> str:
    normalized = str(value).strip()
    if normalized == "*":
        return "*"
    mapping = {
        "0": "Sun",
        "1": "Mon",
        "2": "Tue",
        "3": "Wed",
        "4": "Thu",
        "5": "Fri",
        "6": "Sat",
        "7": "Sun",
    }
    if normalized not in mapping:
        raise ValueError(f"unsupported cron weekday token: {value!r}.")
    return mapping[normalized]


def _cron_dow_range_to_systemd_weekday(value: str) -> str:
    start, end = value.split("-", 1)
    return f"{_cron_dow_single_to_systemd_weekday(value=start)}..{_cron_dow_single_to_systemd_weekday(value=end)}"


def _select_profiles(
    *,
    profile_ids: Sequence[str] | None,
    include_full_recovery: bool,
) -> tuple[dict[str, str], ...]:
    if profile_ids is not None and len(tuple(profile_ids)) == 0:
        raise ValueError("at least one profile_id is required when --profile-ids is provided.")
    requested_profile_ids = (
        [_normalize_profile_id(profile_id) for profile_id in profile_ids]
        if profile_ids is not None
        else [profile.profile_id for profile in OPERATING_DATA_RUN_PROFILES if profile.profile_id != "full-recovery"]
    )
    for normalized_profile_id in requested_profile_ids:
        if normalized_profile_id not in OPERATING_DATA_RUN_PROFILE_IDS:
            raise ValueError(f"unsupported operating data run profile: {normalized_profile_id!r}.")
    if include_full_recovery and "full-recovery" not in requested_profile_ids:
        requested_profile_ids.append("full-recovery")
    if not requested_profile_ids:
        raise ValueError("no operating-data profiles were selected.")

    selected_profiles: list[dict[str, str]] = []
    seen = set()
    for profile_id in requested_profile_ids:
        profile = _find_profile(profile_id)
        if profile_id in seen:
            continue
        selected_profiles.append(
            {
                "profile_id": profile.profile_id,
                "label": profile.label,
                "cadence": profile.cadence,
                "recommended_schedule": profile.recommended_schedule,
            }
        )
        seen.add(profile_id)
    if not selected_profiles:
        raise ValueError("no operating-data profiles were selected.")
    return tuple(selected_profiles)


def _normalize_target(value: str) -> str:
    target = str(value).strip()
    if target not in SERVER_SCHEDULER_TARGETS:
        raise ValueError(f"scheduler_target must be one of: {', '.join(SERVER_SCHEDULER_TARGETS)}")
    return target


def _normalize_profile_id(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError("profile_id must not be empty.")
    return normalized


def _find_profile(profile_id: str):
    normalized = _normalize_profile_id(profile_id)
    for profile in OPERATING_DATA_RUN_PROFILES:
        if profile.profile_id == normalized:
            return profile
    raise ValueError(f"Unsupported operating data run profile: {profile_id!r}.")


def _build_operating_data_run_command_argv(
    *,
    repo_root: Path,
    runtime_root: Path,
    data_operations_env_file: Path,
    profile_id: str,
    timeout_seconds: int,
    python_executable: str | Path | None,
    execute: bool,
    output_path: Path,
) -> tuple[str, ...]:
    python = _resolve_python_executable(runtime_root=runtime_root, python_executable=python_executable)
    command = [
        python,
        "-m",
        "stockanalysis.operations.cli",
        "operating-data-run",
        "--repo-root",
        str(repo_root),
        "--runtime-root",
        str(runtime_root),
        "--data-operations-env-file",
        str(data_operations_env_file),
        "--profile",
        profile_id,
        "--timeout-seconds",
        str(timeout_seconds),
        "--output",
        str(output_path),
    ]
    if execute:
        command.append("--execute")
    return tuple(command)


def _target_manifest_preview(
    *,
    target: str,
    job_name: str,
    schedule: str,
    command_argv: Sequence[str],
    shell_command: str,
    repo_root: Path,
    env_file_path: Path,
    profile_id: str,
    systemd_user: str | None = None,
    systemd_group: str | None = None,
    systemd_home: str | None = None,
) -> dict[str, object]:
    if target == "cron":
        return {
            "kind": "crontab_line_preview",
            "value": f"{schedule} cd {shlex.quote(str(repo_root))} && {shell_command}",
        }
    if target == "systemd":
        return {
            "kind": "systemd_unit_timer_preview",
            "service_name": f"{job_name}-{profile_id}.service",
            "timer_name": f"{job_name}-{profile_id}.timer",
            "working_directory": str(repo_root),
            "environment_file": str(env_file_path),
            "run_user": systemd_user or "",
            "run_group": systemd_group or "",
            "run_home": systemd_home or "",
            "exec_start_preview": shlex.join(command_argv),
            "timer_calendar_preview": schedule,
        }
    if target == "kubernetes_cronjob":
        return {
            "kind": "kubernetes_cronjob_preview",
            "metadata_name": job_name,
            "profile_id": profile_id,
            "schedule": schedule,
            "image": "stockanalysis-operations:latest",
            "env_from_secret_or_config_map": "repo_outside_runtime_env_mount_required",
            "command_preview": tuple(redact_command_argv(command_argv)),
        }
    if target == "managed_scheduler":
        return {
            "kind": "managed_scheduler_command_job_preview",
            "job_name": job_name,
            "profile_id": profile_id,
            "schedule": schedule,
            "working_directory": str(repo_root),
            "env_file_reference": str(env_file_path),
            "command_preview": shell_command,
        }
    raise ValueError(f"unsupported scheduler target: {target}")


def _shell_command(*, repo_root: Path, command_argv: Sequence[str]) -> str:
    return f"PYTHONPATH={shlex.quote(str(repo_root / 'src'))} {shlex.join(command_argv)}"


def _run_system_command_text(argv: Sequence[str]) -> str:
    try:
        result = subprocess.run(
            [str(item) for item in argv],
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError:
        return ""
    return result.stdout.strip()


def _resolve_python_executable(*, runtime_root: Path, python_executable: str | Path | None) -> str:
    if python_executable:
        return str(Path(python_executable).expanduser())
    runtime_python = runtime_root / "venv" / "bin" / "python"
    if runtime_python.is_file():
        return str(runtime_python)
    return "python3"


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    repo_root = Path(str(payload.get("repo_root", ""))).expanduser().resolve() if payload.get("repo_root") else None
    for token in FORBIDDEN_PROFILE_SCHEDULER_TOKENS:
        if token in lower_text:
            raise ValueError("operating data profile scheduler invocation payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value, repo_root=repo_root):
            raise ValueError("operating data profile scheduler payload must not reference repo-inside env files.")


def _looks_like_repo_inside_env(value: str, *, repo_root: Path | None) -> bool:
    path = Path(value)
    if not path.name.endswith(".env") or repo_root is None:
        return False
    try:
        path.expanduser().resolve().relative_to(repo_root)
    except ValueError:
        return False
    return True


def _walk_values(value: object) -> list[object]:
    if isinstance(value, Mapping):
        items: list[object] = []
        for child in value.values():
            items.extend(_walk_values(child))
        return items
    if isinstance(value, list | tuple):
        items = []
        for child in value:
            items.extend(_walk_values(child))
        return items
    if isinstance(value, str):
        return [value]
    return []
