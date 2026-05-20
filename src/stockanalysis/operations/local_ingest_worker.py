from __future__ import annotations

import json
import time
from collections.abc import Callable
from collections.abc import Mapping as MappingABC
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from stockanalysis.operations.manual_local_ingest_smoke import (
    DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS,
    build_manual_local_ingest_smoke_report,
)
from stockanalysis.operations.path_policy import resolve_existing_file, resolve_output_path


SmokeBuilder = Callable[..., dict[str, object]]
SleepFn = Callable[[float], None]
LOCAL_INGEST_WORKER_REPORT_ENV = "STOCKANALYSIS_LOCAL_INGEST_WORKER_REPORT"


def run_local_ingest_worker(
    *,
    repo_root: str | Path | None = None,
    runtime_root: str | Path,
    data_operations_env_file: str | Path | None = None,
    artifact_root: str | Path | None = None,
    job_ids: Sequence[str] | None = None,
    execute: bool = False,
    max_cycles: int = 1,
    interval_seconds: float = 0.0,
    timeout_seconds: int = 1800,
    python_executable: str | Path | None = None,
    smoke_output_path: str | Path | None = None,
    stop_on_failure: bool = True,
    smoke_builder: SmokeBuilder = build_manual_local_ingest_smoke_report,
    sleep_fn: SleepFn = time.sleep,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    if max_cycles <= 0:
        raise ValueError("max_cycles must be positive")
    if interval_seconds < 0:
        raise ValueError("interval_seconds must not be negative")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    selected_job_ids = tuple(job_ids) if job_ids is not None else DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS
    resolved_smoke_output_path = (
        resolve_output_path(
            smoke_output_path,
            label="local ingest worker latest smoke output",
            repo_root=repo_root,
            require_repo_outside=True,
        )
        if smoke_output_path
        else None
    )

    started_at = generated_at or datetime.now(timezone.utc)
    cycles: list[dict[str, object]] = []

    for cycle_number in range(1, max_cycles + 1):
        cycle_started_at = datetime.now(timezone.utc)
        smoke_report = smoke_builder(
            repo_root=repo_root,
            runtime_root=runtime_root,
            data_operations_env_file=data_operations_env_file,
            artifact_root=artifact_root,
            job_ids=selected_job_ids,
            execute=execute,
            timeout_seconds=timeout_seconds,
            python_executable=python_executable,
        )
        if resolved_smoke_output_path is not None:
            resolved_smoke_output_path.write_text(
                json.dumps(smoke_report, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        cycles.append(_summarize_cycle(cycle_number=cycle_number, started_at=cycle_started_at, smoke_report=smoke_report))

        if smoke_report.get("smoke_status") == "failed" and stop_on_failure:
            break
        if cycle_number < max_cycles:
            sleep_fn(interval_seconds)

    failed_cycle_count = sum(1 for cycle in cycles if cycle.get("smoke_status") == "failed")
    worker_status = _worker_status(execute=execute, failed_cycle_count=failed_cycle_count)
    report = {
        "report_name": "local_ingest_worker",
        "generated_at": _format_timestamp(started_at),
        "runtime_mode": "local_first",
        "worker_status": worker_status,
        "execute": execute,
        "job_ids": list(selected_job_ids),
        "max_cycles": max_cycles,
        "completed_cycle_count": len(cycles),
        "failed_cycle_count": failed_cycle_count,
        "interval_seconds": interval_seconds,
        "stop_on_failure": stop_on_failure,
        "latest_smoke_output_path": str(resolved_smoke_output_path) if resolved_smoke_output_path else "",
        "cycles": cycles,
        "codex_host_mutation_allowed": False,
        "launchagents_install_allowed": False,
        "scheduler_scope": "local_process_loop_only",
        "next_actions": _next_actions(worker_status=worker_status, execute=execute),
    }
    _assert_secret_free_payload(report)
    return report


def _summarize_cycle(*, cycle_number: int, started_at: datetime, smoke_report: dict[str, object]) -> dict[str, object]:
    artifact_runs = smoke_report.get("artifact_runs")
    artifact_run_count = len(artifact_runs) if isinstance(artifact_runs, list) else 0
    return {
        "cycle_number": cycle_number,
        "started_at": _format_timestamp(started_at),
        "smoke_status": str(smoke_report.get("smoke_status") or "unknown"),
        "runtime_status": str(smoke_report.get("runtime_status") or ""),
        "execute": smoke_report.get("execute") is True,
        "job_count": int(smoke_report.get("job_count") or 0),
        "failed_job_count": int(smoke_report.get("failed_job_count") or 0),
        "artifact_run_count": artifact_run_count,
    }


def load_local_ingest_worker_visibility_report(
    *,
    report_path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    selected_report_path = str(
        report_path
        if report_path is not None
        else (env if env is not None else {}).get(LOCAL_INGEST_WORKER_REPORT_ENV, "")
    ).strip()
    base = {
        "status": "not_configured",
        "execute": False,
        "generated_at": "",
        "completed_cycle_count": 0,
        "failed_cycle_count": 0,
        "max_cycles": 0,
        "interval_seconds": 0.0,
        "stop_on_failure": True,
        "job_ids": [],
        "latest_smoke_output_path": "",
        "cycles": [],
        "next_actions": ["run local-ingest-worker-run --output outside the repository"],
        "source": "not_configured",
    }
    if not selected_report_path:
        return base

    candidate = Path(selected_report_path).expanduser()
    if not candidate.is_file():
        return {
            **base,
            "status": "missing_report",
            "source": "missing_report",
            "next_actions": ["regenerate local ingest worker summary report"],
        }

    try:
        resolved_report_path = resolve_existing_file(
            candidate,
            label="local ingest worker report",
            repo_root=repo_root,
            require_repo_outside=True,
        )
        payload = json.loads(resolved_report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {
            **base,
            "status": "invalid_report",
            "source": "invalid_report",
            "next_actions": ["regenerate local ingest worker summary report"],
        }

    if not isinstance(payload, dict) or payload.get("report_name") != "local_ingest_worker":
        return {
            **base,
            "status": "invalid_report",
            "source": "invalid_report",
            "next_actions": ["regenerate local ingest worker summary report"],
        }

    visibility = {
        "status": str(payload.get("worker_status") or "unknown"),
        "execute": payload.get("execute") is True,
        "generated_at": str(payload.get("generated_at") or ""),
        "completed_cycle_count": int(payload.get("completed_cycle_count") or 0),
        "failed_cycle_count": int(payload.get("failed_cycle_count") or 0),
        "max_cycles": int(payload.get("max_cycles") or 0),
        "interval_seconds": float(payload.get("interval_seconds") or 0.0),
        "stop_on_failure": payload.get("stop_on_failure") is not False,
        "job_ids": [str(item) for item in _as_scalar_list(payload.get("job_ids"))],
        "latest_smoke_output_path": str(payload.get("latest_smoke_output_path") or ""),
        "cycles": [_cycle_visibility(item) for item in _as_mapping_list(payload.get("cycles"))],
        "next_actions": [str(item) for item in _as_scalar_list(payload.get("next_actions"))],
        "source": "local_ingest_worker_report",
    }
    _assert_secret_free_payload(visibility)
    return visibility


def _cycle_visibility(cycle: Mapping[str, object]) -> dict[str, object]:
    return {
        "cycle_number": int(cycle.get("cycle_number") or 0),
        "started_at": str(cycle.get("started_at") or ""),
        "smoke_status": str(cycle.get("smoke_status") or ""),
        "runtime_status": str(cycle.get("runtime_status") or ""),
        "execute": cycle.get("execute") is True,
        "job_count": int(cycle.get("job_count") or 0),
        "failed_job_count": int(cycle.get("failed_job_count") or 0),
        "artifact_run_count": int(cycle.get("artifact_run_count") or 0),
    }


def _as_mapping_list(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, MappingABC)]


def _as_scalar_list(value: object) -> list[object]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str | int | float | bool)]


def _worker_status(*, execute: bool, failed_cycle_count: int) -> str:
    if failed_cycle_count:
        return "failed"
    if execute:
        return "completed"
    return "preview_not_executed"


def _next_actions(*, worker_status: str, execute: bool) -> list[str]:
    if worker_status == "failed":
        return ["inspect latest smoke output and failed artifact stderr paths before restarting the worker"]
    if not execute:
        return ["review worker preview, then rerun with --execute and bounded --max-cycles if local repetition is intended"]
    return ["open /data-health and verify the latest local ingest worker cycle"]


def _assert_secret_free_payload(payload: dict[str, object]) -> None:
    text = json.dumps(payload, sort_keys=True)
    forbidden_markers = (
        "postgresql://",
        "postgres://",
        "hidden-",
        "token-",
        "api-key-",
        "runtime_pass",
    )
    for marker in forbidden_markers:
        if marker in text:
            raise ValueError("Local ingest worker report contains a secret-like value.")


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
