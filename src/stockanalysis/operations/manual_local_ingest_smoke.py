from __future__ import annotations

import json
import sys
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Sequence

from stockanalysis.operations.artifact_runner import redact_command_argv, run_data_operation_artifact_command
from stockanalysis.operations.cadence import DATA_OPERATIONS_ARTIFACT_ROOT_ENV
from stockanalysis.operations.env_file import load_env_file_values
from stockanalysis.operations.local_runtime_status import (
    DEFAULT_LOCAL_RUNTIME_ROOT,
    build_local_first_runtime_status_report,
)
from stockanalysis.operations.path_policy import ensure_repo_outside, resolve_existing_file, resolve_output_path


DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS = (
    "market-price-daily",
    "news-rss-daily",
    "event-intelligence-weekly",
)
MANUAL_LOCAL_INGEST_SMOKE_REPORT_ENV = "STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT"

ArtifactRunner = Callable[..., dict[str, object]]


@dataclass(frozen=True)
class ManualLocalIngestJob:
    job_id: str
    label: str
    command_argv: tuple[str, ...]

    def as_plan(self) -> dict[str, object]:
        return {
            "job_id": self.job_id,
            "label": self.label,
            "command_argv": redact_command_argv(self.command_argv),
        }


def build_manual_local_ingest_smoke_report(
    *,
    repo_root: str | Path | None = None,
    runtime_root: str | Path = DEFAULT_LOCAL_RUNTIME_ROOT,
    data_operations_env_file: str | Path | None = None,
    artifact_root: str | Path | None = None,
    job_ids: Sequence[str] | None = None,
    execute: bool = False,
    timeout_seconds: int = 1800,
    python_executable: str | Path | None = None,
    runner: ArtifactRunner = run_data_operation_artifact_command,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    runtime_path = Path(runtime_root).expanduser().resolve()
    data_env_path = _resolve_data_env_file(
        runtime_root=runtime_path,
        data_operations_env_file=data_operations_env_file,
        repo_root=repo_root,
    )
    env_values = load_env_file_values(data_env_path)
    artifact_root_path = _resolve_artifact_root(
        explicit_artifact_root=artifact_root,
        env_values=env_values,
        repo_root=repo_root,
    )
    selected_job_ids = tuple(job_ids) if job_ids is not None else DEFAULT_MANUAL_LOCAL_INGEST_JOB_IDS
    resolved_python = _resolve_python_executable(runtime_path=runtime_path, python_executable=python_executable)
    jobs = [
        build_manual_local_ingest_job(
            job_id=job_id,
            data_operations_env_file=data_env_path,
            python_executable=resolved_python,
        )
        for job_id in selected_job_ids
    ]
    runtime_status = build_local_first_runtime_status_report(
        repo_root=repo_root,
        runtime_root=runtime_path,
        data_operations_env_file=data_env_path,
        skip_http_probes=True,
    )
    report: dict[str, object] = {
        "report_name": "manual_local_ingest_smoke",
        "generated_at": _format_timestamp(generated_at or datetime.now(timezone.utc)),
        "runtime_mode": "local_first",
        "execute": execute,
        "smoke_status": "running" if execute else "preview_not_executed",
        "runtime_status": runtime_status.get("overall_status"),
        "data_operations_env_file": str(data_env_path),
        "artifact_root": str(artifact_root_path),
        "python_executable": str(resolved_python),
        "job_count": len(jobs),
        "planned_jobs": [job.as_plan() for job in jobs],
        "artifact_runs": [],
        "codex_host_mutation_allowed": False,
        "launchagents_install_allowed": False,
        "secrets_policy": "values_redacted_env_names_only",
        "write_boundary": "manual_execute_required",
        "next_actions": [],
    }
    if not execute:
        report["next_actions"] = ["review planned_jobs, then rerun with --execute if local ingest smoke should write data"]
        _assert_secret_free_payload(report)
        return report

    artifact_runs: list[dict[str, object]] = []
    for job in jobs:
        artifact_runs.append(
            runner(
                job_id=job.job_id,
                artifact_root=artifact_root_path,
                command_argv=job.command_argv,
                timeout_seconds=timeout_seconds,
            )
        )
    failed_runs = [run for run in artifact_runs if run.get("status") != "succeeded" or int(run.get("exit_code", 1)) != 0]
    report["artifact_runs"] = [_artifact_run_summary(run) for run in artifact_runs]
    report["smoke_status"] = "failed" if failed_runs else "passed"
    report["failed_job_count"] = len(failed_runs)
    report["next_actions"] = (
        ["inspect failed artifact metadata/stderr paths"] if failed_runs else ["open /data-health and verify latest pipeline state"]
    )
    _assert_secret_free_payload(report)
    return report


def build_manual_local_ingest_job(
    *,
    job_id: str,
    data_operations_env_file: Path,
    python_executable: str | Path | None = None,
) -> ManualLocalIngestJob:
    python_bin = str(python_executable or sys.executable)
    env_file = str(data_operations_env_file)
    if job_id == "market-price-daily":
        return ManualLocalIngestJob(
            job_id=job_id,
            label="daily market price ingest",
            command_argv=(
                python_bin,
                "-m",
                "stockanalysis.operations.cli",
                "market-price-daily-run",
                "--env-file",
                env_file,
                "--skip-if-fresh",
            ),
        )
    if job_id == "news-rss-daily":
        return ManualLocalIngestJob(
            job_id=job_id,
            label="intraday free RSS news ingest",
            command_argv=(
                python_bin,
                "-m",
                "stockanalysis.operations.cli",
                "news-rss-daily-run",
                "--env-file",
                env_file,
            ),
        )
    if job_id == "event-intelligence-weekly":
        return ManualLocalIngestJob(
            job_id=job_id,
            label="intraday Codex OAuth news AI evidence",
            command_argv=(
                python_bin,
                "-m",
                "stockanalysis.operations.cli",
                "news-rss-ai-extract-run",
                "--env-file",
                env_file,
                "--provider",
                "codex_oauth",
                "--limit",
                "10",
                "--execute",
            ),
        )
    raise ValueError(f"Unsupported manual local ingest smoke job_id: {job_id}")


def load_manual_local_ingest_smoke_visibility_report(
    *,
    report_path: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, object]:
    selected_report_path = str(
        report_path
        if report_path is not None
        else (env if env is not None else {}).get(MANUAL_LOCAL_INGEST_SMOKE_REPORT_ENV, "")
    ).strip()
    base = {
        "status": "not_configured",
        "execute": False,
        "generated_at": "",
        "runtime_status": "",
        "artifact_root": "",
        "job_count": 0,
        "planned_job_ids": [],
        "artifact_runs": [],
        "failed_job_count": 0,
        "next_actions": ["run manual-local-ingest-smoke --output outside the repository"],
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
            "next_actions": ["regenerate manual-local-ingest-smoke summary report"],
        }

    try:
        resolved_report_path = resolve_existing_file(
            candidate,
            label="manual local ingest smoke report",
            repo_root=repo_root,
            require_repo_outside=True,
        )
        payload = json.loads(resolved_report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {
            **base,
            "status": "invalid_report",
            "source": "invalid_report",
            "next_actions": ["regenerate manual-local-ingest-smoke summary report"],
        }

    if not isinstance(payload, dict) or payload.get("report_name") != "manual_local_ingest_smoke":
        return {
            **base,
            "status": "invalid_report",
            "source": "invalid_report",
            "next_actions": ["regenerate manual-local-ingest-smoke summary report"],
        }

    planned_job_ids = [
        str(item.get("job_id") or "")
        for item in _as_mapping_list(payload.get("planned_jobs"))
        if str(item.get("job_id") or "")
    ]
    artifact_runs = [_artifact_run_summary(item) for item in _as_mapping_list(payload.get("artifact_runs"))]
    status = str(payload.get("smoke_status") or "unknown")
    visibility = {
        "status": status,
        "execute": payload.get("execute") is True,
        "generated_at": str(payload.get("generated_at") or ""),
        "runtime_status": str(payload.get("runtime_status") or ""),
        "artifact_root": str(payload.get("artifact_root") or ""),
        "job_count": int(payload.get("job_count") or len(planned_job_ids)),
        "planned_job_ids": planned_job_ids,
        "artifact_runs": artifact_runs,
        "failed_job_count": int(payload.get("failed_job_count") or 0),
        "next_actions": [str(item) for item in _as_scalar_list(payload.get("next_actions"))],
        "source": "manual_local_ingest_smoke_report",
    }
    _assert_secret_free_payload(visibility)
    return visibility


def _resolve_python_executable(*, runtime_path: Path, python_executable: str | Path | None) -> str:
    if python_executable is not None:
        return str(python_executable)
    runtime_python = runtime_path / "venv" / "bin" / "python"
    if runtime_python.is_file():
        return str(runtime_python)
    return sys.executable


def _resolve_data_env_file(
    *,
    runtime_root: Path,
    data_operations_env_file: str | Path | None,
    repo_root: str | Path | None,
) -> Path:
    selected = Path(data_operations_env_file).expanduser() if data_operations_env_file else runtime_root / "data-operations.env"
    return resolve_existing_file(
        selected,
        label="data operations env file",
        repo_root=repo_root,
        require_repo_outside=True,
    )


def _resolve_artifact_root(
    *,
    explicit_artifact_root: str | Path | None,
    env_values: Mapping[str, str],
    repo_root: str | Path | None,
) -> Path:
    selected = explicit_artifact_root or env_values.get(DATA_OPERATIONS_ARTIFACT_ROOT_ENV)
    if not selected:
        raise ValueError(f"Missing {DATA_OPERATIONS_ARTIFACT_ROOT_ENV}; provide --artifact-root or configure env file.")
    path = resolve_output_path(
        selected,
        label="manual local ingest smoke artifact root",
        repo_root=repo_root,
        require_repo_outside=True,
    )
    ensure_repo_outside(path, repo_root=repo_root, label="manual local ingest smoke artifact root")
    return path


def _artifact_run_summary(run: Mapping[str, object]) -> dict[str, object]:
    return {
        "job_id": run.get("job_id", ""),
        "pipeline_name": run.get("pipeline_name", ""),
        "status": run.get("status", ""),
        "exit_code": int(run.get("exit_code", 1)),
        "artifact_dir": run.get("artifact_dir", ""),
        "metadata_path": run.get("metadata_path", ""),
        "stdout_path": run.get("stdout_path", ""),
        "stderr_path": run.get("stderr_path", ""),
        "stdout_json_path": run.get("stdout_json_path", ""),
    }


def _as_mapping_list(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, MappingABC)]


def _as_scalar_list(value: object) -> list[object]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str | int | float | bool)]


def _assert_secret_free_payload(payload: Mapping[str, object]) -> None:
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
            raise ValueError("Manual local ingest smoke report contains a secret-like value.")


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
