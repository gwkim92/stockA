from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


REQUIRED_APPROVAL_COMMANDS = {
    "install -m 600",
    "launchctl bootstrap",
    "launchctl kickstart",
    "launchctl print",
}

REQUIRED_RISK_ACKNOWLEDGEMENTS = {
    "host_scheduler_state_change",
    "recurring_data_operation_execution",
    "rollback_required_if_first_run_fails",
}

FORBIDDEN_APPROVAL_TOKENS = (
    "postgresql://",
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "FRED_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "api-key",
    "bearer ",
    "password",
)


def build_data_operations_scheduler_activation_approval_gate_report(
    *,
    operator_dry_run_report: Mapping[str, object],
    approval_record: Mapping[str, object] | None = None,
    approval_record_path: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    _validate_operator_dry_run_report(operator_dry_run_report)
    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    base_report = {
        "report_name": "data_operations_scheduler_activation_approval_gate",
        "job_id": str(operator_dry_run_report["job_id"]),
        "pipeline_name": str(operator_dry_run_report.get("pipeline_name", "")),
        "domain": str(operator_dry_run_report.get("domain", "")),
        "cadence": str(operator_dry_run_report.get("cadence", "")),
        "operator_dry_run": "passed",
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "operator_dry_run_report_path": _evidence_report_path(operator_dry_run_report),
        "approval_record_path": approval_record_path,
        "secrets_policy": "approval_metadata_only_no_env_values",
    }

    if approval_record is None:
        return {
            **base_report,
            "approval_gate": "blocked_pending_manual_approval",
            "activation_allowed": False,
            "approval_decision": "missing",
            "required_next_step": "provide_repo_outside_approval_record",
            "manual_next_step": "data-operations-live-scheduler-activation-request",
        }

    _validate_approval_record(
        approval_record=approval_record,
        job_id=str(operator_dry_run_report["job_id"]),
        operator_dry_run_report_path=_evidence_report_path(operator_dry_run_report),
    )

    report = {
        **base_report,
        "approval_gate": "approved_for_manual_activation",
        "activation_allowed": True,
        "approval_decision": "approved",
        "operator": str(approval_record["operator"]),
        "approved_at": str(approval_record["approved_at"]),
        "activation_window": str(approval_record["activation_window"]),
        "rollback_owner": str(approval_record["rollback_owner"]),
        "acknowledged_commands": sorted(str(item) for item in approval_record["acknowledged_commands"]),
        "acknowledged_risks": sorted(str(item) for item in approval_record["acknowledged_risks"]),
        "required_next_step": "operator_may_request_live_scheduler_activation",
        "manual_next_step": "data-operations-live-scheduler-activation-request",
    }
    _assert_secret_free(report)
    return report


def _validate_operator_dry_run_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_scheduler_operator_dry_run":
        raise ValueError("operator dry-run report has unexpected report_name.")
    if report.get("operator_dry_run") != "passed":
        raise ValueError("operator dry-run report must be passed.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("operator dry-run must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("operator dry-run must not execute launchctl.")
    if report.get("child_command_executed") is not False:
        raise ValueError("operator dry-run must not execute child command.")
    if report.get("requires_manual_approval") is not True:
        raise ValueError("operator dry-run must require manual approval.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("operator dry-run report must include job_id.")


def _validate_approval_record(
    *,
    approval_record: Mapping[str, object],
    job_id: str,
    operator_dry_run_report_path: str,
) -> None:
    _assert_secret_free(approval_record)
    if approval_record.get("approval_record") != "data_operations_scheduler_activation_approval":
        raise ValueError("approval record has unexpected approval_record value.")
    if approval_record.get("approval_decision") != "approved":
        raise ValueError("approval record decision must be approved.")
    for field in ("operator", "approved_at", "activation_window", "rollback_owner"):
        if not str(approval_record.get(field, "")).strip():
            raise ValueError(f"approval record missing required field: {field}")
    if approval_record.get("job_id") != job_id:
        raise ValueError("approval record job_id must match operator dry-run report.")

    referenced_report = str(approval_record.get("operator_dry_run_report", "")).strip()
    if not referenced_report:
        raise ValueError("approval record must reference operator_dry_run_report.")
    if operator_dry_run_report_path and referenced_report != operator_dry_run_report_path:
        raise ValueError("approval record must reference the same operator dry-run report path.")

    _parse_iso_timestamp(str(approval_record["approved_at"]))

    acknowledged_commands = {str(item) for item in _as_list(approval_record.get("acknowledged_commands"))}
    missing_commands = sorted(REQUIRED_APPROVAL_COMMANDS - acknowledged_commands)
    if missing_commands:
        raise ValueError(f"approval record missing acknowledged commands: {', '.join(missing_commands)}")

    acknowledged_risks = {str(item) for item in _as_list(approval_record.get("acknowledged_risks"))}
    missing_risks = sorted(REQUIRED_RISK_ACKNOWLEDGEMENTS - acknowledged_risks)
    if missing_risks:
        raise ValueError(f"approval record missing risk acknowledgements: {', '.join(missing_risks)}")


def _evidence_report_path(report: Mapping[str, object]) -> str:
    evidence_paths = report.get("evidence_paths")
    if isinstance(evidence_paths, Mapping):
        value = evidence_paths.get("operator_dry_run_report")
        if value:
            return str(value)
    return ""


def _parse_iso_timestamp(value: str) -> None:
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("approved_at must be an ISO timestamp.") from exc


def _as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("approval record acknowledgement fields must be lists.")
    return value


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    for token in FORBIDDEN_APPROVAL_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("approval gate payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("approval gate payload must not reference repo-inside env files.")


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
