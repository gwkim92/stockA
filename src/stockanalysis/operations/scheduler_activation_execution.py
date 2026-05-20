from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


CONFIRM_HOST_ACTIVATION_EXECUTION = "confirm_host_activation_execution"
ABORT_HOST_ACTIVATION_EXECUTION = "abort_host_activation_execution"
ALLOWED_HOST_ACTIVATION_CONFIRMATIONS = {
    CONFIRM_HOST_ACTIVATION_EXECUTION,
    ABORT_HOST_ACTIVATION_EXECUTION,
}
REQUIRED_HOST_MUTATION_ACKNOWLEDGEMENTS = {
    "host_launchagents_write",
    "launchctl_bootstrap",
    "launchctl_kickstart",
    "launchctl_print",
    "rollback_required_if_activation_fails",
    "recurring_data_operation_execution",
}
FORBIDDEN_HOST_ACTIVATION_EXECUTION_TOKENS = (
    "postgresql://",
    "api-key",
    "bearer ",
    "password",
)


def build_data_operations_live_scheduler_host_activation_execution_report(
    *,
    execution_final_preflight_report: Mapping[str, object],
    confirmation_record: Mapping[str, object] | None = None,
    execution_final_preflight_report_path: str = "",
    confirmation_record_path: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    _validate_execution_final_preflight_report(execution_final_preflight_report)
    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    execution_commands = _as_string_list(execution_final_preflight_report.get("execution_command_preview"))
    rollback_commands = _as_string_list(execution_final_preflight_report.get("rollback_command_preview"))
    base_report = {
        "report_name": "data_operations_live_scheduler_host_activation_execution",
        "job_id": str(execution_final_preflight_report["job_id"]),
        "pipeline_name": str(execution_final_preflight_report.get("pipeline_name", "")),
        "domain": str(execution_final_preflight_report.get("domain", "")),
        "cadence": str(execution_final_preflight_report.get("cadence", "")),
        "rendered_label": str(execution_final_preflight_report.get("rendered_label", "")),
        "host_plist_path_preview": str(execution_final_preflight_report.get("host_plist_path_preview", "")),
        "execution_final_preflight_report_path": execution_final_preflight_report_path,
        "confirmation_record_path": confirmation_record_path,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_performed": False,
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "execution_command_preview": execution_commands,
        "rollback_command_preview": rollback_commands,
        "secrets_policy": "host_activation_execution_metadata_only_no_env_values",
    }

    if confirmation_record is None:
        report = {
            **base_report,
            "execution_gate": "blocked_pending_explicit_host_mutation_confirmation",
            "host_activation_execution_allowed_in_this_task": False,
            "host_activation_execution_allowed_for_manual_operator": False,
            "required_next_step": "provide_repo_outside_host_activation_execution_confirmation_record",
            "manual_next_step": "data-operations-live-scheduler-host-activation-execution",
        }
        _assert_secret_free(report)
        return report

    _validate_confirmation_record(
        confirmation_record=confirmation_record,
        job_id=str(execution_final_preflight_report["job_id"]),
        execution_final_preflight_report_path=execution_final_preflight_report_path,
    )
    confirmation = str(confirmation_record["confirmation"])
    if confirmation == ABORT_HOST_ACTIVATION_EXECUTION:
        report = {
            **base_report,
            "execution_gate": "aborted_by_explicit_host_mutation_confirmation",
            "host_activation_execution_allowed_in_this_task": False,
            "host_activation_execution_allowed_for_manual_operator": False,
            "confirmer": str(confirmation_record["confirmer"]),
            "confirmed_at": str(confirmation_record["confirmed_at"]),
            "confirmation_scope": str(confirmation_record["confirmation_scope"]),
            "operator_note": str(confirmation_record.get("operator_note", "")),
            "required_next_step": "do_not_execute_host_activation_revisit_final_preflight",
            "manual_next_step": "data-operations-live-scheduler-host-activation-execution-final-preflight",
        }
        _assert_secret_free(report)
        return report

    report = {
        **base_report,
        "execution_gate": "confirmed_for_manual_host_mutation_not_executed_by_this_task",
        "host_activation_execution_allowed_in_this_task": False,
        "host_activation_execution_allowed_for_manual_operator": True,
        "confirmer": str(confirmation_record["confirmer"]),
        "confirmed_at": str(confirmation_record["confirmed_at"]),
        "confirmation_scope": str(confirmation_record["confirmation_scope"]),
        "acknowledged_final_preflight_state": str(confirmation_record["acknowledged_final_preflight_state"]),
        "acknowledged_mutation_boundary": sorted(
            str(item) for item in confirmation_record["acknowledged_mutation_boundary"]
        ),
        "operator_note": str(confirmation_record.get("operator_note", "")),
        "required_next_step": "manual_operator_executes_reviewed_host_commands_outside_this_task",
        "manual_next_step": "manual-host-scheduler-activation",
    }
    _assert_secret_free(report)
    return report


def _validate_execution_final_preflight_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_live_scheduler_host_activation_execution_final_preflight":
        raise ValueError("execution final preflight report has unexpected report_name.")
    if report.get("execution_final_preflight") != "passed_ready_for_host_activation_execution_task":
        raise ValueError("execution final preflight report must be passed_ready_for_host_activation_execution_task.")
    if report.get("host_activation_execution_allowed_for_next_task") is not True:
        raise ValueError("execution final preflight report must allow the next execution task.")
    if report.get("host_activation_execution_allowed_in_this_task") is not False:
        raise ValueError("execution final preflight report must not allow execution in that task.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("execution final preflight report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("execution final preflight report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("execution final preflight report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("execution final preflight report must not execute child command.")
    if report.get("manual_next_step") != "data-operations-live-scheduler-host-activation-execution":
        raise ValueError("execution final preflight report must point to the host activation execution task.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("execution final preflight report must include job_id.")
    if not _as_string_list(report.get("execution_command_preview")):
        raise ValueError("execution final preflight report must include execution command previews.")
    if not _as_string_list(report.get("rollback_command_preview")):
        raise ValueError("execution final preflight report must include rollback command previews.")
    _assert_secret_free(report)


def _validate_confirmation_record(
    *,
    confirmation_record: Mapping[str, object],
    job_id: str,
    execution_final_preflight_report_path: str,
) -> None:
    _assert_secret_free(confirmation_record)
    if confirmation_record.get("confirmation_record") != "data_operations_live_scheduler_host_activation_execution_confirmation":
        raise ValueError("confirmation record has unexpected confirmation_record value.")
    if confirmation_record.get("confirmation") not in ALLOWED_HOST_ACTIVATION_CONFIRMATIONS:
        raise ValueError("confirmation record confirmation must be confirm_host_activation_execution or abort_host_activation_execution.")
    for field in ("confirmer", "confirmed_at", "confirmation_scope", "acknowledged_final_preflight_state"):
        if not str(confirmation_record.get(field, "")).strip():
            raise ValueError(f"confirmation record missing required field: {field}")
    if confirmation_record.get("job_id") != job_id:
        raise ValueError("confirmation record job_id must match execution final preflight report.")
    if confirmation_record.get("confirmation_scope") != "data_operations_scheduler_host_activation_execution":
        raise ValueError("confirmation record confirmation_scope must be data_operations_scheduler_host_activation_execution.")
    if confirmation_record.get("acknowledged_final_preflight_state") != "passed_ready_for_host_activation_execution_task":
        raise ValueError("confirmation record must acknowledge passed_ready_for_host_activation_execution_task.")

    referenced_report = str(confirmation_record.get("execution_final_preflight_report", "")).strip()
    if not referenced_report:
        raise ValueError("confirmation record must reference execution_final_preflight_report.")
    if execution_final_preflight_report_path and _normalize_path(referenced_report) != _normalize_path(
        execution_final_preflight_report_path
    ):
        raise ValueError("confirmation record must reference the same execution final preflight report path.")

    _parse_iso_timestamp(str(confirmation_record["confirmed_at"]))
    acknowledged = {str(item) for item in _as_list(confirmation_record.get("acknowledged_mutation_boundary"))}
    missing_acknowledgements = sorted(REQUIRED_HOST_MUTATION_ACKNOWLEDGEMENTS - acknowledged)
    if missing_acknowledgements:
        raise ValueError(f"confirmation record missing mutation acknowledgements: {', '.join(missing_acknowledgements)}")


def _parse_iso_timestamp(value: str) -> None:
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("confirmed_at must be an ISO timestamp.") from exc


def _as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("confirmation fields must be lists.")
    return value


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("command previews must be lists.")
    return [str(item) for item in value]


def _normalize_path(value: str) -> str:
    return str(Path(value).expanduser().resolve())


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    for token in FORBIDDEN_HOST_ACTIVATION_EXECUTION_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("host activation execution payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("host activation execution payload must not reference repo-inside env files.")


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
