from __future__ import annotations

import json
import os
import selectors
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import urlsplit, urlunsplit
from stockanalysis.operations.batch_runtime import atomic_json

from stockanalysis.operations.cadence import (
    DATA_OPERATIONS_ARTIFACT_ROOT_ENV,
    get_data_operation_cadence,
)


DEFAULT_TIMEOUT_SECONDS = 60 * 60
MAX_OUTPUT_BYTES = 16 * 1024 * 1024  # per stream, written to disk incrementally


class _BatchInterrupted(Exception):
    """Do not use InterruptedError: selectors treats it as a retryable syscall."""

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

    progress_path = run_dir / "progress.json"
    atomic_json(progress_path, {"status": "running", "job_id": job.job_id,
                               "started_at": _format_timestamp(started_at_value), "timeout_seconds": timeout_seconds})
    status, exit_code = _capture_bounded_process(command, stdout_path, stderr_path,
                                               env=env, cwd=cwd, timeout_seconds=timeout_seconds)
    stdout = stdout_path.read_text(encoding="utf-8", errors="replace")

    completed_at_value = _coerce_utc(completed_at or datetime.now(timezone.utc))
    stdout_format = _write_stdout_json_if_possible(stdout, stdout_json_path)

    metadata = {
        "report_name": "data_operations_artifact_run",
        "job_id": job.job_id,
        "pipeline_name": job.pipeline_name,
        "domain": job.domain,
        "cadence": job.cadence,
        "status": status,
        "exit_code": exit_code,
        "timeout": status == "timeout",
        "output_limit_bytes_per_stream": MAX_OUTPUT_BYTES,
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
    atomic_json(metadata_path, metadata)
    atomic_json(progress_path, {"status": status, "job_id": job.job_id,
                               "ended_at": _format_timestamp(completed_at_value), "exit_code": exit_code})
    return metadata


def _stop_process_group(process: subprocess.Popen) -> None:
    # Batch children must not survive their owning command's timeout/cancellation.
    # systemd KillMode=control-group additionally covers descendants that create a new session.
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    try:
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGKILL)
        elif process.poll() is None:
            process.kill()
    except ProcessLookupError:
        pass
    process.wait(timeout=5)


def _capture_bounded_process(command, stdout_path, stderr_path, *, env, cwd, timeout_seconds):
    process = None
    old_handler = None
    def interrupted(signum, frame):
        raise _BatchInterrupted("Batch runner terminated")
    try:
        if threading.current_thread() is threading.main_thread():
            old_handler = signal.signal(signal.SIGTERM, interrupted)
        with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
            try:
                process = subprocess.Popen(command, cwd=str(cwd) if cwd is not None else None,
                    env=dict(env) if env is not None else None, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    start_new_session=os.name == "posix")
            except OSError as exc:
                stderr_file.write((type(exc).__name__ + ": command could not be started\n").encode())
                return "failed", 127
            deadline = time.monotonic() + timeout_seconds
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ, [stdout_file, 0])
                selector.register(process.stderr, selectors.EVENT_READ, [stderr_file, 0])
                while selector.get_map() or process.poll() is None:
                    if time.monotonic() >= deadline:
                        _stop_process_group(process)
                        return "timeout", 124
                    for key, _ in selector.select(timeout=min(.1, max(0, deadline - time.monotonic()))):
                        chunk = os.read(key.fileobj.fileno(), 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        output, size = key.data
                        remaining = MAX_OUTPUT_BYTES - size
                        output.write(chunk[:remaining])
                        key.data[1] += min(remaining, len(chunk))
                        if len(chunk) > remaining:
                            _stop_process_group(process)
                            return "output_limit", 125
                code = process.wait()
                return ("succeeded" if code == 0 else "failed"), code
    except (_BatchInterrupted, KeyboardInterrupt):
        if process is not None:
            _stop_process_group(process)
        return "interrupted", 143
    except BaseException:
        if process is not None:
            _stop_process_group(process)
        raise
    finally:
        if process is not None:
            if process.stdout is not None:
                process.stdout.close()
            if process.stderr is not None:
                process.stderr.close()
        if old_handler is not None:
            signal.signal(signal.SIGTERM, old_handler)


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
    candidate.mkdir(parents=True, mode=0o700)
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
