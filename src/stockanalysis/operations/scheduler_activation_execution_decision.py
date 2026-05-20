from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping

from stockanalysis.operations.scheduler_activation_execution_request import (
    APPROVE_EXECUTION_DECISION,
    DENY_EXECUTION_DECISION,
)


ALLOWED_EXECUTION_DECISIONS = {
    APPROVE_EXECUTION_DECISION,
    DENY_EXECUTION_DECISION,
}

REQUIRED_EXECUTION_ACKNOWLEDGEMENTS = {
    "host_launchagents_write",
    "launchctl_bootstrap",
    "launchctl_kickstart",
    "launchctl_print",
    "rollback_required_if_activation_fails",
    "recurring_data_operation_execution",
}

FORBIDDEN_EXECUTION_DECISION_TOKENS = (
    "postgresql://",
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "FRED_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "api-key",
    "bearer ",
    "password",
)


def build_data_operations_live_scheduler_host_activation_execution_decision_report(
    *,
    execution_request_report: Mapping[str, object],
    decision_record: Mapping[str, object] | None = None,
    execution_request_report_path: str = "",
    decision_record_path: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    _validate_execution_request_report(execution_request_report)
    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    base_report = {
        "report_name": "data_operations_live_scheduler_host_activation_execution_decision",
        "job_id": str(execution_request_report["job_id"]),
        "pipeline_name": str(execution_request_report.get("pipeline_name", "")),
        "domain": str(execution_request_report.get("domain", "")),
        "cadence": str(execution_request_report.get("cadence", "")),
        "execution_request": "pending_explicit_execution_approval",
        "execution_request_report_path": execution_request_report_path,
        "decision_record_path": decision_record_path,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_allowed_in_this_task": False,
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "secrets_policy": "host_activation_execution_decision_metadata_only_no_env_values",
    }

    if decision_record is None:
        report = {
            **base_report,
            "decision_gate": "blocked_pending_execution_decision",
            "user_decision": "missing",
            "host_activation_execution_allowed_for_next_task": False,
            "required_next_step": "provide_repo_outside_host_activation_execution_decision_record",
            "manual_next_step": "data-operations-live-scheduler-host-activation-execution-decision",
        }
        _assert_secret_free(report)
        return report

    _validate_decision_record(
        decision_record=decision_record,
        job_id=str(execution_request_report["job_id"]),
        execution_request_report_path=execution_request_report_path,
    )
    decision = str(decision_record["decision"])
    if decision == APPROVE_EXECUTION_DECISION:
        report = {
            **base_report,
            "decision_gate": "approved_for_host_activation_execution_final_preflight",
            "user_decision": decision,
            "host_activation_execution_allowed_for_next_task": True,
            "decider": str(decision_record["decider"]),
            "decided_at": str(decision_record["decided_at"]),
            "decision_scope": str(decision_record["decision_scope"]),
            "acknowledged_request_state": str(decision_record["acknowledged_request_state"]),
            "acknowledged_mutation_boundary": sorted(
                str(item) for item in decision_record["acknowledged_mutation_boundary"]
            ),
            "operator_note": str(decision_record.get("operator_note", "")),
            "required_next_step": "run_host_activation_execution_final_preflight_before_execution",
            "manual_next_step": "data-operations-live-scheduler-host-activation-execution-final-preflight",
        }
    else:
        report = {
            **base_report,
            "decision_gate": "denied_host_activation_execution",
            "user_decision": decision,
            "host_activation_execution_allowed_for_next_task": False,
            "decider": str(decision_record["decider"]),
            "decided_at": str(decision_record["decided_at"]),
            "decision_scope": str(decision_record["decision_scope"]),
            "acknowledged_request_state": str(decision_record["acknowledged_request_state"]),
            "acknowledged_mutation_boundary": sorted(
                str(item) for item in decision_record["acknowledged_mutation_boundary"]
            ),
            "operator_note": str(decision_record.get("operator_note", "")),
            "required_next_step": "do_not_execute_scheduler_revisit_execution_request",
            "manual_next_step": "data-operations-live-scheduler-host-activation-execution-request",
        }
    _assert_secret_free(report)
    return report


def _validate_execution_request_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_live_scheduler_host_activation_execution_request":
        raise ValueError("execution request report has unexpected report_name.")
    if report.get("execution_request") != "pending_explicit_execution_approval":
        raise ValueError("execution request report must be pending_explicit_execution_approval.")
    if report.get("requires_explicit_execution_approval") is not True:
        raise ValueError("execution request report must require explicit execution approval.")
    if report.get("execution_allowed_by_plan") is not True:
        raise ValueError("execution request report must be allowed by host activation plan.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("execution request report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("execution request report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("execution request report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("execution request report must not execute child command.")
    if report.get("host_activation_execution_allowed_in_this_task") is not False:
        raise ValueError("execution request report must not allow execution in that task.")
    if report.get("manual_next_step") != "data-operations-live-scheduler-host-activation-execution-decision":
        raise ValueError("execution request report must point to the execution decision task.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("execution request report must include job_id.")

    requested_values = {str(item) for item in _as_list(report.get("requested_user_decision_values"))}
    missing = sorted(ALLOWED_EXECUTION_DECISIONS - requested_values)
    if missing:
        raise ValueError(f"execution request report missing decision values: {', '.join(missing)}")
    if not _as_list(report.get("execution_command_preview")):
        raise ValueError("execution request report must include execution_command_preview.")
    if not _as_list(report.get("rollback_command_preview")):
        raise ValueError("execution request report must include rollback_command_preview.")
    _assert_secret_free(report)


def _validate_decision_record(
    *,
    decision_record: Mapping[str, object],
    job_id: str,
    execution_request_report_path: str,
) -> None:
    _assert_secret_free(decision_record)
    if decision_record.get("decision_record") != "data_operations_live_scheduler_host_activation_execution_decision":
        raise ValueError("decision record has unexpected decision_record value.")
    if decision_record.get("decision") not in ALLOWED_EXECUTION_DECISIONS:
        raise ValueError("decision record decision must be approve_host_activation_execution or deny_host_activation_execution.")
    for field in ("decider", "decided_at", "decision_scope", "acknowledged_request_state"):
        if not str(decision_record.get(field, "")).strip():
            raise ValueError(f"decision record missing required field: {field}")
    if decision_record.get("job_id") != job_id:
        raise ValueError("decision record job_id must match execution request report.")
    if decision_record.get("decision_scope") != "data_operations_scheduler_host_activation_execution":
        raise ValueError("decision record decision_scope must be data_operations_scheduler_host_activation_execution.")
    if decision_record.get("acknowledged_request_state") != "pending_explicit_execution_approval":
        raise ValueError("decision record must acknowledge pending_explicit_execution_approval.")

    referenced_report = str(decision_record.get("execution_request_report", "")).strip()
    if not referenced_report:
        raise ValueError("decision record must reference execution_request_report.")
    if execution_request_report_path and _normalize_path(referenced_report) != _normalize_path(execution_request_report_path):
        raise ValueError("decision record must reference the same execution request report path.")

    _parse_iso_timestamp(str(decision_record["decided_at"]))

    acknowledged = {str(item) for item in _as_list(decision_record.get("acknowledged_mutation_boundary"))}
    missing_acknowledgements = sorted(REQUIRED_EXECUTION_ACKNOWLEDGEMENTS - acknowledged)
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
    for token in FORBIDDEN_EXECUTION_DECISION_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("host activation execution decision payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("host activation execution decision payload must not reference repo-inside env files.")


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
