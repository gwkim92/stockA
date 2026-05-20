from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


APPROVE_EXACT_HOST_SCHEDULER_ACTIVATION = "approve_exact_host_scheduler_activation"
ABORT_EXACT_HOST_SCHEDULER_ACTIVATION = "abort_exact_host_scheduler_activation"
ALLOWED_MANUAL_HOST_SCHEDULER_APPROVALS = {
    APPROVE_EXACT_HOST_SCHEDULER_ACTIVATION,
    ABORT_EXACT_HOST_SCHEDULER_ACTIVATION,
}
REQUIRED_HOST_MUTATION_ACKNOWLEDGEMENTS = {
    "host_launchagents_write",
    "launchctl_bootstrap",
    "launchctl_kickstart",
    "launchctl_print",
    "rollback_required_if_activation_fails",
    "recurring_data_operation_execution",
}
REQUIRED_OPERATOR_RESPONSIBILITIES = {
    "operator_runs_commands_outside_codex",
    "operator_records_exit_statuses",
    "operator_collects_launchctl_print_evidence",
    "operator_collects_first_run_artifacts",
    "operator_can_execute_rollback",
}
FORBIDDEN_MANUAL_HOST_ACTIVATION_TOKENS = (
    "postgresql://",
    "api-key",
    "bearer ",
    "password",
)


def build_manual_host_scheduler_activation_explicit_approval_report(
    *,
    host_activation_execution_report: Mapping[str, object],
    approval_record: Mapping[str, object] | None = None,
    host_activation_execution_report_path: str = "",
    approval_record_path: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    _validate_host_activation_execution_report(host_activation_execution_report)
    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    exact_execution_commands = _as_string_list(host_activation_execution_report.get("execution_command_preview"))
    exact_rollback_commands = _as_string_list(host_activation_execution_report.get("rollback_command_preview"))
    base_report = {
        "report_name": "manual_host_scheduler_activation_explicit_approval",
        "job_id": str(host_activation_execution_report["job_id"]),
        "pipeline_name": str(host_activation_execution_report.get("pipeline_name", "")),
        "domain": str(host_activation_execution_report.get("domain", "")),
        "cadence": str(host_activation_execution_report.get("cadence", "")),
        "rendered_label": str(host_activation_execution_report.get("rendered_label", "")),
        "host_plist_path_preview": str(host_activation_execution_report.get("host_plist_path_preview", "")),
        "host_activation_execution_report_path": host_activation_execution_report_path,
        "approval_record_path": approval_record_path,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_performed": False,
        "codex_host_mutation_allowed": False,
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "exact_execution_commands": exact_execution_commands,
        "exact_rollback_commands": exact_rollback_commands,
        "secrets_policy": "manual_host_scheduler_activation_metadata_only_no_env_values",
    }

    if approval_record is None:
        report = {
            **base_report,
            "approval_gate": "blocked_pending_exact_host_command_approval",
            "host_activation_allowed_for_manual_operator": False,
            "required_next_step": "collect_explicit_user_approval_for_exact_host_commands",
            "manual_next_step": "manual-host-scheduler-activation-explicit-approval",
            "approval_record_template": _approval_record_template(
                host_activation_execution_report=host_activation_execution_report,
                host_activation_execution_report_path=host_activation_execution_report_path,
                exact_execution_commands=exact_execution_commands,
                exact_rollback_commands=exact_rollback_commands,
            ),
        }
        _assert_secret_free(report)
        return report

    _validate_approval_record(
        approval_record=approval_record,
        job_id=str(host_activation_execution_report["job_id"]),
        host_activation_execution_report_path=host_activation_execution_report_path,
        exact_execution_commands=exact_execution_commands,
        exact_rollback_commands=exact_rollback_commands,
    )
    approval = str(approval_record["approval"])
    if approval == ABORT_EXACT_HOST_SCHEDULER_ACTIVATION:
        report = {
            **base_report,
            "approval_gate": "aborted_manual_host_scheduler_activation",
            "host_activation_allowed_for_manual_operator": False,
            "approver": str(approval_record["approver"]),
            "approved_at": str(approval_record["approved_at"]),
            "approval_scope": str(approval_record["approval_scope"]),
            "operator_note": str(approval_record.get("operator_note", "")),
            "required_next_step": "do_not_execute_host_commands_revisit_execution_final_preflight",
            "manual_next_step": "data-operations-live-scheduler-host-activation-execution-final-preflight",
        }
        _assert_secret_free(report)
        return report

    report = {
        **base_report,
        "approval_gate": "approved_for_manual_operator_host_activation_not_executed_by_codex",
        "host_activation_allowed_for_manual_operator": True,
        "approver": str(approval_record["approver"]),
        "approved_at": str(approval_record["approved_at"]),
        "approval_scope": str(approval_record["approval_scope"]),
        "acknowledged_execution_gate": str(approval_record["acknowledged_execution_gate"]),
        "acknowledged_mutation_boundary": sorted(str(item) for item in approval_record["acknowledged_mutation_boundary"]),
        "acknowledged_operator_responsibility": sorted(
            str(item) for item in approval_record["acknowledged_operator_responsibility"]
        ),
        "operator_note": str(approval_record.get("operator_note", "")),
        "required_next_step": "operator_runs_exact_commands_outside_codex_and_collects_evidence",
        "manual_next_step": "manual-host-scheduler-activation-operator-evidence",
    }
    _assert_secret_free(report)
    return report


def _validate_host_activation_execution_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_live_scheduler_host_activation_execution":
        raise ValueError("host activation execution report has unexpected report_name.")
    if report.get("execution_gate") != "confirmed_for_manual_host_mutation_not_executed_by_this_task":
        raise ValueError("host activation execution report must be confirmed for manual host mutation.")
    if report.get("host_activation_execution_allowed_for_manual_operator") is not True:
        raise ValueError("host activation execution report must allow a manual operator.")
    if report.get("host_activation_execution_allowed_in_this_task") is not False:
        raise ValueError("host activation execution report must not allow execution inside Codex.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("host activation execution report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("host activation execution report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("host activation execution report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("host activation execution report must not execute child command.")
    if report.get("host_activation_execution_performed") is not False:
        raise ValueError("host activation execution report must not perform host activation execution.")
    if report.get("manual_next_step") != "manual-host-scheduler-activation":
        raise ValueError("host activation execution report must hand off to manual host scheduler activation.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("host activation execution report must include job_id.")
    if not _as_string_list(report.get("execution_command_preview")):
        raise ValueError("host activation execution report must include exact execution command previews.")
    if not _as_string_list(report.get("rollback_command_preview")):
        raise ValueError("host activation execution report must include exact rollback command previews.")
    _assert_secret_free(report)


def _approval_record_template(
    *,
    host_activation_execution_report: Mapping[str, object],
    host_activation_execution_report_path: str,
    exact_execution_commands: list[str],
    exact_rollback_commands: list[str],
) -> dict[str, object]:
    return {
        "approval_record": "manual_host_scheduler_activation_explicit_approval",
        "approval": APPROVE_EXACT_HOST_SCHEDULER_ACTIVATION,
        "approver": "operator-handle",
        "approved_at": "YYYY-MM-DDTHH:MM:SSZ",
        "job_id": str(host_activation_execution_report["job_id"]),
        "host_activation_execution_report": host_activation_execution_report_path,
        "approval_scope": "manual_host_scheduler_activation",
        "acknowledged_execution_gate": "confirmed_for_manual_host_mutation_not_executed_by_this_task",
        "approved_exact_execution_commands": exact_execution_commands,
        "approved_exact_rollback_commands": exact_rollback_commands,
        "acknowledged_mutation_boundary": sorted(REQUIRED_HOST_MUTATION_ACKNOWLEDGEMENTS),
        "acknowledged_operator_responsibility": sorted(REQUIRED_OPERATOR_RESPONSIBILITIES),
        "operator_note": "",
    }


def _validate_approval_record(
    *,
    approval_record: Mapping[str, object],
    job_id: str,
    host_activation_execution_report_path: str,
    exact_execution_commands: list[str],
    exact_rollback_commands: list[str],
) -> None:
    _assert_secret_free(approval_record)
    if approval_record.get("approval_record") != "manual_host_scheduler_activation_explicit_approval":
        raise ValueError("approval record has unexpected approval_record value.")
    if approval_record.get("approval") not in ALLOWED_MANUAL_HOST_SCHEDULER_APPROVALS:
        raise ValueError(
            "approval record approval must be approve_exact_host_scheduler_activation or abort_exact_host_scheduler_activation."
        )
    for field in ("approver", "approved_at", "approval_scope", "acknowledged_execution_gate"):
        if not str(approval_record.get(field, "")).strip():
            raise ValueError(f"approval record missing required field: {field}")
    if approval_record.get("job_id") != job_id:
        raise ValueError("approval record job_id must match host activation execution report.")
    if approval_record.get("approval_scope") != "manual_host_scheduler_activation":
        raise ValueError("approval record approval_scope must be manual_host_scheduler_activation.")
    if approval_record.get("acknowledged_execution_gate") != "confirmed_for_manual_host_mutation_not_executed_by_this_task":
        raise ValueError("approval record must acknowledge confirmed manual host mutation gate.")

    referenced_report = str(approval_record.get("host_activation_execution_report", "")).strip()
    if not referenced_report:
        raise ValueError("approval record must reference host_activation_execution_report.")
    if host_activation_execution_report_path and _normalize_path(referenced_report) != _normalize_path(
        host_activation_execution_report_path
    ):
        raise ValueError("approval record must reference the same host activation execution report path.")

    approved_execution_commands = _as_string_list(approval_record.get("approved_exact_execution_commands"))
    approved_rollback_commands = _as_string_list(approval_record.get("approved_exact_rollback_commands"))
    if approved_execution_commands != exact_execution_commands:
        raise ValueError("approval record exact execution commands must match the host activation execution report.")
    if approved_rollback_commands != exact_rollback_commands:
        raise ValueError("approval record exact rollback commands must match the host activation execution report.")

    _parse_iso_timestamp(str(approval_record["approved_at"]))
    acknowledged = {str(item) for item in _as_list(approval_record.get("acknowledged_mutation_boundary"))}
    missing_acknowledgements = sorted(REQUIRED_HOST_MUTATION_ACKNOWLEDGEMENTS - acknowledged)
    if missing_acknowledgements:
        raise ValueError(f"approval record missing mutation acknowledgements: {', '.join(missing_acknowledgements)}")
    responsibilities = {str(item) for item in _as_list(approval_record.get("acknowledged_operator_responsibility"))}
    missing_responsibilities = sorted(REQUIRED_OPERATOR_RESPONSIBILITIES - responsibilities)
    if missing_responsibilities:
        raise ValueError(f"approval record missing operator responsibilities: {', '.join(missing_responsibilities)}")


def _parse_iso_timestamp(value: str) -> None:
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError("approved_at must be an ISO timestamp.") from exc


def _as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("approval fields must be lists.")
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
    for token in FORBIDDEN_MANUAL_HOST_ACTIVATION_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("manual host scheduler activation approval payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("manual host scheduler activation approval payload must not reference repo-inside env files.")


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
