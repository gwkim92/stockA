from __future__ import annotations

from datetime import date, datetime, timezone
import re
from typing import Mapping, Sequence

from stockanalysis.operations.artifact_runner import redact_command_argv
from stockanalysis.operations.cadence import get_data_operation_cadence


DEFAULT_SKIP_REASON = "configured_skip_date"
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def build_data_operations_scheduler_preflight_report(
    *,
    job_id: str,
    readiness_report: Mapping[str, object],
    command_argv: Sequence[str],
    run_date: str,
    skip_dates: str | Sequence[str] = (),
    skip_reason: str = DEFAULT_SKIP_REASON,
    timeout_seconds: int = 3600,
) -> dict[str, object]:
    if readiness_report.get("runtime_env_readiness") != "passed":
        raise ValueError("Scheduler preflight requires passed data operations env readiness.")
    command = tuple(str(part) for part in command_argv)
    if not command:
        raise ValueError("Scheduler command must not be empty.")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive.")

    job = get_data_operation_cadence(job_id)
    run_date_value = _parse_iso_date(run_date, name="run_date")
    skip_date_values = _parse_skip_dates(skip_dates)
    would_skip = run_date_value in skip_date_values

    return {
        "report_name": "data_operations_scheduler_preflight",
        "preflight": "passed",
        "scheduler_activation": "boundary_only_not_installed",
        "job_id": job.job_id,
        "pipeline_name": job.pipeline_name,
        "domain": job.domain,
        "cadence": job.cadence,
        "timezone": "America/New_York",
        "run_date": run_date_value.isoformat(),
        "skip_dates": [value.isoformat() for value in skip_date_values],
        "would_skip": would_skip,
        "skip_reason": skip_reason,
        "timeout_seconds": timeout_seconds,
        "artifact_root_configured": True,
        "runtime_env_readiness": "passed",
        "validated_env_groups": list(readiness_report.get("validated_env_groups", [])),
        "required_env_groups": list(job.required_env_groups),
        "command_argv": redact_command_argv(command),
        "secrets_policy": "values_redacted_env_names_only",
    }


def build_data_operations_scheduler_skip_report(
    *,
    job_id: str,
    run_date: str,
    skip_dates: str | Sequence[str],
    skip_reason: str = DEFAULT_SKIP_REASON,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    job = get_data_operation_cadence(job_id)
    run_date_value = _parse_iso_date(run_date, name="run_date")
    skip_date_values = _parse_skip_dates(skip_dates)
    if run_date_value not in skip_date_values:
        raise ValueError("Skip report requires run_date to be present in skip_dates.")
    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    return {
        "report_name": "data_operations_scheduler_skip",
        "status": "skipped",
        "scheduler_activation": "boundary_only_not_installed",
        "job_id": job.job_id,
        "pipeline_name": job.pipeline_name,
        "domain": job.domain,
        "cadence": job.cadence,
        "run_date": run_date_value.isoformat(),
        "skip_dates": [value.isoformat() for value in skip_date_values],
        "skip_reason": skip_reason,
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
    }


def _parse_skip_dates(value: str | Sequence[str]) -> tuple[date, ...]:
    if isinstance(value, str):
        tokens = value.replace(",", " ").split()
    else:
        tokens = [str(item) for item in value]
    return tuple(_parse_iso_date(token, name="skip_dates") for token in tokens if token)


def _parse_iso_date(value: str, *, name: str) -> date:
    if not _ISO_DATE_RE.match(value):
        raise ValueError(f"{name} must be ISO date YYYY-MM-DD.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be ISO date YYYY-MM-DD.") from exc
