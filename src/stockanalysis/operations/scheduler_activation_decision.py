from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


APPROVE_DECISION = "approve_live_scheduler_activation"
DENY_DECISION = "deny_live_scheduler_activation"
ALLOWED_DECISIONS = {APPROVE_DECISION, DENY_DECISION}

REQUIRED_DECISION_ACKNOWLEDGEMENTS = {
    "host_launchagents_write",
    "launchctl_bootstrap",
    "recurring_data_operation_execution",
    "rollback_required_if_activation_fails",
}

FORBIDDEN_DECISION_TOKENS = (
    "postgresql://",
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "FRED_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "api-key",
    "bearer ",
    "password",
)


def build_data_operations_live_scheduler_activation_user_decision_report(
    *,
    activation_request_report: Mapping[str, object],
    decision_record: Mapping[str, object] | None = None,
    activation_request_report_path: str = "",
    decision_record_path: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    _validate_activation_request_report(activation_request_report)
    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    base_report = {
        "report_name": "data_operations_live_scheduler_activation_user_decision",
        "job_id": str(activation_request_report["job_id"]),
        "pipeline_name": str(activation_request_report.get("pipeline_name", "")),
        "domain": str(activation_request_report.get("domain", "")),
        "cadence": str(activation_request_report.get("cadence", "")),
        "activation_request": "pending_explicit_user_approval",
        "activation_request_report_path": activation_request_report_path,
        "decision_record_path": decision_record_path,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "activation_execution_allowed_in_this_task": False,
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "secrets_policy": "user_decision_metadata_only_no_env_values",
    }

    if decision_record is None:
        return {
            **base_report,
            "decision_gate": "blocked_pending_user_decision",
            "user_decision": "missing",
            "activation_allowed_for_next_task": False,
            "required_next_step": "provide_repo_outside_user_decision_record",
            "manual_next_step": "data-operations-live-scheduler-activation-user-decision",
        }

    _validate_decision_record(
        decision_record=decision_record,
        job_id=str(activation_request_report["job_id"]),
        activation_request_report_path=activation_request_report_path,
    )
    decision = str(decision_record["decision"])
    if decision == APPROVE_DECISION:
        report = {
            **base_report,
            "decision_gate": "approved_for_live_scheduler_activation_final_preflight",
            "user_decision": decision,
            "activation_allowed_for_next_task": True,
            "decider": str(decision_record["decider"]),
            "decided_at": str(decision_record["decided_at"]),
            "decision_scope": str(decision_record["decision_scope"]),
            "acknowledged_request_state": str(decision_record["acknowledged_request_state"]),
            "acknowledged_mutation_boundary": sorted(
                str(item) for item in decision_record["acknowledged_mutation_boundary"]
            ),
            "operator_note": str(decision_record.get("operator_note", "")),
            "required_next_step": "run_final_preflight_before_host_activation",
            "manual_next_step": "data-operations-live-scheduler-activation-final-preflight",
        }
    else:
        report = {
            **base_report,
            "decision_gate": "denied_live_scheduler_activation",
            "user_decision": decision,
            "activation_allowed_for_next_task": False,
            "decider": str(decision_record["decider"]),
            "decided_at": str(decision_record["decided_at"]),
            "decision_scope": str(decision_record["decision_scope"]),
            "acknowledged_request_state": str(decision_record["acknowledged_request_state"]),
            "acknowledged_mutation_boundary": sorted(
                str(item) for item in decision_record["acknowledged_mutation_boundary"]
            ),
            "operator_note": str(decision_record.get("operator_note", "")),
            "required_next_step": "do_not_activate_scheduler_revisit_request_evidence",
            "manual_next_step": "data-operations-live-scheduler-activation-request",
        }
    _assert_secret_free(report)
    return report


def _validate_activation_request_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_live_scheduler_activation_request":
        raise ValueError("activation request report has unexpected report_name.")
    if report.get("activation_request") != "pending_explicit_user_approval":
        raise ValueError("activation request report must be pending explicit user approval.")
    if report.get("requires_explicit_user_approval") is not True:
        raise ValueError("activation request report must require explicit user approval.")
    if report.get("activation_allowed_by_gate") is not True:
        raise ValueError("activation request report must be allowed by activation gate.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("activation request report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("activation request report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("activation request report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("activation request report must not execute child command.")
    if report.get("manual_next_step") != "data-operations-live-scheduler-activation-user-decision":
        raise ValueError("activation request report must point to the user decision task.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("activation request report must include job_id.")

    requested_values = {str(item) for item in _as_list(report.get("requested_user_decision_values"))}
    missing = sorted(ALLOWED_DECISIONS - requested_values)
    if missing:
        raise ValueError(f"activation request report missing decision values: {', '.join(missing)}")

    _assert_secret_free(report)


def _validate_decision_record(
    *,
    decision_record: Mapping[str, object],
    job_id: str,
    activation_request_report_path: str,
) -> None:
    _assert_secret_free(decision_record)
    if decision_record.get("decision_record") != "data_operations_live_scheduler_activation_user_decision":
        raise ValueError("decision record has unexpected decision_record value.")
    if decision_record.get("decision") not in ALLOWED_DECISIONS:
        raise ValueError("decision record decision must be approve_live_scheduler_activation or deny_live_scheduler_activation.")
    for field in ("decider", "decided_at", "decision_scope", "acknowledged_request_state"):
        if not str(decision_record.get(field, "")).strip():
            raise ValueError(f"decision record missing required field: {field}")
    if decision_record.get("job_id") != job_id:
        raise ValueError("decision record job_id must match activation request report.")
    if decision_record.get("decision_scope") != "data_operations_scheduler_host_activation":
        raise ValueError("decision record decision_scope must be data_operations_scheduler_host_activation.")
    if decision_record.get("acknowledged_request_state") != "pending_explicit_user_approval":
        raise ValueError("decision record must acknowledge pending_explicit_user_approval.")

    referenced_report = str(decision_record.get("activation_request_report", "")).strip()
    if not referenced_report:
        raise ValueError("decision record must reference activation_request_report.")
    if activation_request_report_path and _normalize_path(referenced_report) != _normalize_path(activation_request_report_path):
        raise ValueError("decision record must reference the same activation request report path.")

    _parse_iso_timestamp(str(decision_record["decided_at"]))

    acknowledged = {str(item) for item in _as_list(decision_record.get("acknowledged_mutation_boundary"))}
    missing_acknowledgements = sorted(REQUIRED_DECISION_ACKNOWLEDGEMENTS - acknowledged)
    if missing_acknowledgements:
        raise ValueError(f"decision record missing mutation acknowledgements: {', '.join(missing_acknowledgements)}")


def _parse_iso_timestamp(value: str) -> None:
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("decided_at must be an ISO timestamp.") from exc


def _as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("decision fields must be lists.")
    return value


def _normalize_path(value: str) -> str:
    return str(Path(value).expanduser().resolve())


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    for token in FORBIDDEN_DECISION_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("activation decision payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("activation decision payload must not reference repo-inside env files.")


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
