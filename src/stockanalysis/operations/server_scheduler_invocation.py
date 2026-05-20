from __future__ import annotations

import json
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from stockanalysis.operations.artifact_runner import redact_command_argv
from stockanalysis.operations.local_runtime_status import DEFAULT_LOCAL_RUNTIME_ROOT
from stockanalysis.operations.manual_local_ingest_smoke import DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS
from stockanalysis.operations.path_policy import (
    ensure_repo_outside,
    resolve_existing_file,
    resolve_output_path,
    resolve_repo_root,
)


SERVER_SCHEDULER_TARGETS = (
    "cron",
    "systemd",
    "kubernetes_cronjob",
    "managed_scheduler",
)
DEFAULT_SERVER_SCHEDULER_SCHEDULE = "30 18 * * 1-5"
DEFAULT_SERVER_SCHEDULER_JOB_NAME = "stockanalysis-local-ingest-worker"
FORBIDDEN_SERVER_SCHEDULER_TOKENS = (
    "postgresql://",
    "api-key=",
    "api_key=",
    "bearer ",
    "password=",
    "sk-",
)


def build_server_scheduler_invocation_plan(
    *,
    scheduler_target: str,
    repo_root: str | Path | None = None,
    runtime_root: str | Path = DEFAULT_LOCAL_RUNTIME_ROOT,
    data_operations_env_file: str | Path,
    worker_report_output: str | Path,
    smoke_output: str | Path,
    artifact_root: str | Path | None = None,
    job_ids: Sequence[str] | None = None,
    worker_execute: bool = False,
    max_cycles: int = 1,
    interval_seconds: float = 0.0,
    timeout_seconds: int = 1800,
    schedule: str = DEFAULT_SERVER_SCHEDULER_SCHEDULE,
    python_executable: str | Path | None = None,
    job_name: str = DEFAULT_SERVER_SCHEDULER_JOB_NAME,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    target = _normalize_target(scheduler_target)
    if max_cycles <= 0:
        raise ValueError("max_cycles must be positive.")
    if interval_seconds < 0:
        raise ValueError("interval_seconds must not be negative.")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive.")
    if not str(schedule).strip():
        raise ValueError("schedule must not be empty.")
    if not str(job_name).strip():
        raise ValueError("job_name must not be empty.")

    repo_root_path = resolve_repo_root(repo_root)
    runtime_root_path = ensure_repo_outside(
        Path(runtime_root).expanduser().resolve(),
        repo_root=repo_root_path,
        label="server scheduler runtime root",
    )
    env_file_path = resolve_existing_file(
        data_operations_env_file,
        label="server scheduler data operations env file",
        repo_root=repo_root_path,
        require_repo_outside=True,
    )
    worker_report_output_path = resolve_output_path(
        worker_report_output,
        label="server scheduler worker report output",
        repo_root=repo_root_path,
        require_repo_outside=True,
    )
    smoke_output_path = resolve_output_path(
        smoke_output,
        label="server scheduler latest smoke output",
        repo_root=repo_root_path,
        require_repo_outside=True,
    )
    artifact_root_path = (
        ensure_repo_outside(
            Path(artifact_root).expanduser().resolve(),
            repo_root=repo_root_path,
            label="server scheduler artifact root",
        )
        if artifact_root
        else None
    )
    selected_job_ids = tuple(job_ids) if job_ids is not None else tuple(DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS)
    for job_id in selected_job_ids:
        if job_id not in DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS:
            raise ValueError(f"unsupported local ingest worker job_id: {job_id}")

    command_argv = _build_worker_command_argv(
        repo_root=repo_root_path,
        runtime_root=runtime_root_path,
        data_operations_env_file=env_file_path,
        worker_report_output=worker_report_output_path,
        smoke_output=smoke_output_path,
        artifact_root=artifact_root_path,
        job_ids=selected_job_ids,
        worker_execute=worker_execute,
        max_cycles=max_cycles,
        interval_seconds=interval_seconds,
        timeout_seconds=timeout_seconds,
        python_executable=python_executable,
    )
    shell_command = _shell_command(repo_root=repo_root_path, command_argv=command_argv)
    generated_at_value = _coerce_utc(generated_at or datetime.now(timezone.utc))

    report = {
        "report_name": "server_scheduler_invocation_boundary",
        "generated_at": _format_timestamp(generated_at_value),
        "scheduler_target": target,
        "scheduler_job_name": str(job_name).strip(),
        "schedule": str(schedule).strip(),
        "scheduler_deployed": False,
        "scheduler_install_allowed_in_this_task": False,
        "host_mutation_allowed": False,
        "launchctl_executed": False,
        "host_install_path_written": False,
        "child_command_executed": False,
        "worker_execute": worker_execute,
        "repo_root": str(repo_root_path),
        "runtime_root": str(runtime_root_path),
        "data_operations_env_file": str(env_file_path),
        "worker_report_output": str(worker_report_output_path),
        "latest_smoke_output": str(smoke_output_path),
        "artifact_root": str(artifact_root_path) if artifact_root_path else "",
        "job_ids": list(selected_job_ids),
        "max_cycles": max_cycles,
        "interval_seconds": interval_seconds,
        "timeout_seconds": timeout_seconds,
        "command_argv_preview": redact_command_argv(command_argv),
        "shell_command_preview": shell_command,
        "target_manifest_preview": _target_manifest_preview(
            target=target,
            job_name=str(job_name).strip(),
            schedule=str(schedule).strip(),
            shell_command=shell_command,
            command_argv=command_argv,
            repo_root=repo_root_path,
            env_file_path=env_file_path,
        ),
        "operator_warnings": [
            "This report is an invocation packet only, not scheduler deployment approval.",
            "Do not paste env values into scheduler manifests; mount or inject the repo-outside env file securely.",
            "Run the worker manually and verify /api/data-health before deploying a recurring scheduler.",
        ],
        "manual_next_step": "server-scheduler-deployment-target-decision",
        "secrets_policy": "paths_and_redacted_commands_only_no_env_values",
    }
    _assert_secret_free(report)
    return report


def render_server_scheduler_invocation_markdown(report: Mapping[str, object]) -> str:
    _assert_secret_free(report)
    lines = [
        "# Server Scheduler Invocation Boundary",
        "",
        f"- target: `{report.get('scheduler_target', '')}`",
        f"- job name: `{report.get('scheduler_job_name', '')}`",
        f"- schedule: `{report.get('schedule', '')}`",
        f"- deployed: `{str(report.get('scheduler_deployed')).lower()}`",
        f"- install allowed in this task: `{str(report.get('scheduler_install_allowed_in_this_task')).lower()}`",
        f"- worker execute mode: `{str(report.get('worker_execute')).lower()}`",
        "",
        "## Command Preview",
        "",
        f"```bash\n{report.get('shell_command_preview', '')}\n```",
        "",
        "## Boundary",
        "",
        "- This packet does not deploy a scheduler.",
        "- It must not execute `launchctl`, write LaunchAgents, or mutate host scheduler state.",
        "- Env values remain outside this report.",
        "",
    ]
    return "\n".join(lines)


def _build_worker_command_argv(
    *,
    repo_root: Path,
    runtime_root: Path,
    data_operations_env_file: Path,
    worker_report_output: Path,
    smoke_output: Path,
    artifact_root: Path | None,
    job_ids: Sequence[str],
    worker_execute: bool,
    max_cycles: int,
    interval_seconds: float,
    timeout_seconds: int,
    python_executable: str | Path | None,
) -> list[str]:
    command = [
        _resolve_python_executable(runtime_root=runtime_root, python_executable=python_executable),
        "-m",
        "stockanalysis.operations.cli",
        "local-ingest-worker-run",
        "--repo-root",
        str(repo_root),
        "--runtime-root",
        str(runtime_root),
        "--data-operations-env-file",
        str(data_operations_env_file),
        "--max-cycles",
        str(max_cycles),
        "--interval-seconds",
        _format_number(interval_seconds),
        "--timeout-seconds",
        str(timeout_seconds),
        "--smoke-output",
        str(smoke_output),
        "--output",
        str(worker_report_output),
    ]
    if artifact_root is not None:
        command.extend(["--artifact-root", str(artifact_root)])
    for job_id in job_ids:
        command.extend(["--job-id", job_id])
    if worker_execute:
        command.append("--execute")
    return command


def _target_manifest_preview(
    *,
    target: str,
    job_name: str,
    schedule: str,
    shell_command: str,
    command_argv: Sequence[str],
    repo_root: Path,
    env_file_path: Path,
) -> dict[str, object]:
    if target == "cron":
        return {
            "kind": "crontab_line_preview",
            "value": f"{schedule} cd {shlex.quote(str(repo_root))} && {shell_command}",
        }
    if target == "systemd":
        return {
            "kind": "systemd_unit_timer_preview",
            "service_name": f"{job_name}.service",
            "timer_name": f"{job_name}.timer",
            "working_directory": str(repo_root),
            "environment_file": str(env_file_path),
            "exec_start_preview": shell_command,
            "timer_calendar_preview": schedule,
        }
    if target == "kubernetes_cronjob":
        return {
            "kind": "kubernetes_cronjob_preview",
            "metadata_name": job_name,
            "schedule": schedule,
            "image": "stockanalysis-operations:latest",
            "env_from_secret_or_config_map": "repo_outside_runtime_env_mount_required",
            "command_preview": list(redact_command_argv(command_argv)),
        }
    if target == "managed_scheduler":
        return {
            "kind": "managed_scheduler_command_job_preview",
            "job_name": job_name,
            "schedule": schedule,
            "working_directory": str(repo_root),
            "env_file_reference": str(env_file_path),
            "command_preview": shell_command,
        }
    raise ValueError(f"unsupported scheduler target: {target}")


def _shell_command(*, repo_root: Path, command_argv: Sequence[str]) -> str:
    return f"PYTHONPATH={shlex.quote(str(repo_root / 'src'))} {shlex.join([str(arg) for arg in command_argv])}"


def _resolve_python_executable(*, runtime_root: Path, python_executable: str | Path | None) -> str:
    if python_executable:
        return str(Path(python_executable).expanduser())
    runtime_python = runtime_root / "venv" / "bin" / "python"
    if runtime_python.is_file():
        return str(runtime_python)
    return "python3"


def _normalize_target(value: str) -> str:
    target = str(value).strip()
    if target not in SERVER_SCHEDULER_TARGETS:
        raise ValueError(f"scheduler_target must be one of: {', '.join(SERVER_SCHEDULER_TARGETS)}")
    return target


def _format_number(value: float) -> str:
    if float(value).is_integer():
        return str(int(value))
    return str(value)


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0)


def _format_timestamp(value: datetime) -> str:
    return _coerce_utc(value).isoformat().replace("+00:00", "Z")


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    for token in FORBIDDEN_SERVER_SCHEDULER_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("server scheduler invocation payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("server scheduler invocation payload must not reference repo-inside env files.")


def _walk_values(value: object) -> list[object]:
    if isinstance(value, Mapping):
        items: list[object] = []
        for child in value.values():
            items.extend(_walk_values(child))
        return items
    if isinstance(value, list):
        items = []
        for child in value:
            items.extend(_walk_values(child))
        return items
    return [value]


def _looks_like_repo_inside_env(value: str) -> bool:
    path = Path(value)
    return path.name.endswith(".env") and "stockanalysis" in path.parts
