from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit

from stockanalysis.operations.cadence import (
    DATA_OPERATIONS_ARTIFACT_ROOT_ENV,
    get_data_operation_cadence,
)


DEFAULT_TIMEOUT_SECONDS = 60 * 60
SECRET_VALUE = "[REDACTED]"
_SENSITIVE_FLAG_MARKERS = (
    "api-key",
    "apikey",
    "authorization",
    "bearer",
    "database-url",
    "database_url",
    "dsn",
    "password",
    "read-token",
    "secret",
    "token",
)


def run_data_operation_artifact_command(
    *,
    job_id: str,
    command_argv: Sequence[str],
    artifact_root: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    cwd: str | Path | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> dict[str, object]:
    job = get_data_operation_cadence(job_id)
    command = tuple(str(part) for part in command_argv)
    if not command:
        raise ValueError("data operation artifact command must not be empty")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    root = _resolve_artifact_root(artifact_root=artifact_root, env=env)
    started_at_value = _coerce_utc(started_at or datetime.now(timezone.utc))
    run_dir = _create_run_dir(root, job_id=job.job_id, started_at=started_at_value)
    stdout_path = run_dir / "stdout.txt"
    stderr_path = run_dir / "stderr.log"
    stdout_json_path = run_dir / "stdout.json"
    metadata_path = run_dir / "metadata.json"

    status = "succeeded"
    timeout = False
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        if exit_code != 0:
            status = "failed"
    except subprocess.TimeoutExpired as exc:
        timeout = True
        status = "timeout"
        exit_code = 124
        stdout = _timeout_output_to_text(exc.stdout)
        stderr = _timeout_output_to_text(exc.stderr)

    completed_at_value = _coerce_utc(completed_at or datetime.now(timezone.utc))
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")
    stdout_format = _write_stdout_json_if_possible(stdout, stdout_json_path)

    metadata = {
        "report_name": "data_operations_artifact_run",
        "job_id": job.job_id,
        "pipeline_name": job.pipeline_name,
        "domain": job.domain,
        "cadence": job.cadence,
        "status": status,
        "exit_code": exit_code,
        "timeout": timeout,
        "timeout_seconds": timeout_seconds,
        "started_at": _format_timestamp(started_at_value),
        "ended_at": _format_timestamp(completed_at_value),
        "duration_ms": max(0, int((completed_at_value - started_at_value).total_seconds() * 1000)),
        "artifact_root_env": DATA_OPERATIONS_ARTIFACT_ROOT_ENV,
        "artifact_dir": str(run_dir),
        "command_argv": redact_command_argv(command),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "stdout_json_path": str(stdout_json_path) if stdout_format == "json" else "",
        "stdout_format": stdout_format,
        "metadata_path": str(metadata_path),
    }
    metadata_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return metadata


def redact_command_argv(command_argv: Sequence[str]) -> list[str]:
    redacted: list[str] = []
    redact_next = False
    for raw_arg in command_argv:
        arg = str(raw_arg)
        if redact_next:
            redacted.append(SECRET_VALUE)
            redact_next = False
            continue

        lower_arg = arg.lower()
        if _is_sensitive_assignment(lower_arg):
            key = arg.split("=", 1)[0]
            redacted.append(f"{key}={SECRET_VALUE}")
            continue
        if _is_sensitive_flag(lower_arg):
            redacted.append(arg)
            if "=" not in arg:
                redact_next = True
            continue
        redacted.append(_redact_url_userinfo(arg))
    return redacted


def _resolve_artifact_root(*, artifact_root: str | Path | None, env: Mapping[str, str] | None) -> Path:
    if artifact_root is not None:
        root = Path(artifact_root)
    else:
        env_mapping = env if env is not None else os.environ
        root_value = env_mapping.get(DATA_OPERATIONS_ARTIFACT_ROOT_ENV)
        if not root_value:
            raise ValueError(f"Missing required environment variable: {DATA_OPERATIONS_ARTIFACT_ROOT_ENV}")
        root = Path(root_value)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _create_run_dir(root: Path, *, job_id: str, started_at: datetime) -> Path:
    base_name = f"{_run_timestamp(started_at)}_{_safe_path_segment(job_id)}"
    candidate = root / base_name
    suffix = 2
    while candidate.exists():
        candidate = root / f"{base_name}-{suffix}"
        suffix += 1
    candidate.mkdir(parents=True)
    return candidate


def _write_stdout_json_if_possible(stdout: str, path: Path) -> str:
    stripped = stdout.strip()
    if not stripped:
        return "empty"
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return "text"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return "json"


def _is_sensitive_assignment(lower_arg: str) -> bool:
    if "=" not in lower_arg:
        return False
    key = lower_arg.split("=", 1)[0].lstrip("-").replace("_", "-")
    return any(marker in key for marker in _SENSITIVE_FLAG_MARKERS)


def _is_sensitive_flag(lower_arg: str) -> bool:
    if not lower_arg.startswith("-"):
        return False
    flag = lower_arg.split("=", 1)[0].lstrip("-").replace("_", "-")
    return any(marker in flag for marker in _SENSITIVE_FLAG_MARKERS)


def _redact_url_userinfo(value: str) -> str:
    if "://" not in value or "@" not in value:
        return value
    parsed = urlsplit(value)
    if "@" not in parsed.netloc:
        return value
    host = parsed.netloc.rsplit("@", 1)[1]
    return urlunsplit((parsed.scheme, f"{SECRET_VALUE}@{host}", parsed.path, parsed.query, parsed.fragment))


def _safe_path_segment(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in value).strip("-") or "job"


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return _coerce_utc(value).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _run_timestamp(value: datetime) -> str:
    return _coerce_utc(value).strftime("%Y%m%dT%H%M%SZ")


def _timeout_output_to_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
