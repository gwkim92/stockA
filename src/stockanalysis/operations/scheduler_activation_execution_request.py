from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


APPROVE_EXECUTION_DECISION = "approve_host_activation_execution"
DENY_EXECUTION_DECISION = "deny_host_activation_execution"
ALLOWED_EXECUTION_DECISIONS = {
    APPROVE_EXECUTION_DECISION,
    DENY_EXECUTION_DECISION,
}

FORBIDDEN_EXECUTION_REQUEST_TOKENS = (
    "postgresql://",
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "FRED_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "api-key",
    "bearer ",
    "password",
)


def build_data_operations_live_scheduler_host_activation_execution_request_report(
    *,
    host_activation_plan_report: Mapping[str, object],
    host_activation_plan_report_path: str = "",
    request_note: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    """Create an explicit execution approval request without mutating host scheduler state."""

    _validate_host_activation_plan_report(host_activation_plan_report)
    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    execution_commands = _extract_step_commands(host_activation_plan_report.get("execution_plan_steps"))
    rollback_commands = _extract_step_commands(host_activation_plan_report.get("rollback_plan_steps"))

    report = {
        "report_name": "data_operations_live_scheduler_host_activation_execution_request",
        "execution_request": "pending_explicit_execution_approval",
        "requested_user_decision_values": sorted(ALLOWED_EXECUTION_DECISIONS),
        "required_user_action": "provide_approve_host_activation_execution_or_deny_host_activation_execution_record",
        "requires_explicit_execution_approval": True,
        "execution_allowed_by_plan": True,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_allowed_in_this_task": False,
        "job_id": str(host_activation_plan_report["job_id"]),
        "pipeline_name": str(host_activation_plan_report.get("pipeline_name", "")),
        "domain": str(host_activation_plan_report.get("domain", "")),
        "cadence": str(host_activation_plan_report.get("cadence", "")),
        "rendered_label": str(host_activation_plan_report.get("rendered_label", "")),
        "host_plist_path_preview": str(host_activation_plan_report.get("host_plist_path_preview", "")),
        "host_activation_plan_report_path": host_activation_plan_report_path,
        "final_preflight_report_path": str(host_activation_plan_report.get("final_preflight_report_path", "")),
        "activation_request_report_path": str(host_activation_plan_report.get("activation_request_report_path", "")),
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "request_note": request_note,
        "execution_command_preview": execution_commands,
        "rollback_command_preview": rollback_commands,
        "acknowledgement_requirements": [
            "host_launchagents_write",
            "launchctl_bootstrap",
            "launchctl_kickstart",
            "launchctl_print",
            "rollback_required_if_activation_fails",
            "recurring_data_operation_execution",
        ],
        "safety_boundary": {
            "writes_host_launchagents": False,
            "executes_launchctl": False,
            "executes_child_command": False,
            "requires_separate_execution_decision_record": True,
        },
        "required_next_step": "provide_repo_outside_host_activation_execution_decision_record",
        "manual_next_step": "data-operations-live-scheduler-host-activation-execution-decision",
        "secrets_policy": "host_activation_execution_request_metadata_only_no_env_values",
    }
    _assert_secret_free(report)
    return report


def _validate_host_activation_plan_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_live_scheduler_host_activation_plan":
        raise ValueError("host activation plan report has unexpected report_name.")
    if report.get("host_activation_plan") != "ready_for_execution_request":
        raise ValueError("host activation plan report must be ready_for_execution_request.")
    if report.get("activation_allowed_for_execution_request") is not True:
        raise ValueError("host activation plan report must allow execution request.")
    if report.get("host_activation_execution_allowed_in_this_task") is not False:
        raise ValueError("host activation plan report must not allow execution in that task.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("host activation plan report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("host activation plan report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("host activation plan report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("host activation plan report must not execute child command.")
    if report.get("manual_next_step") != "data-operations-live-scheduler-host-activation-execution-request":
        raise ValueError("host activation plan report must point to the execution request task.")
    for field in ("job_id", "rendered_label", "host_plist_path_preview"):
        if not str(report.get(field, "")).strip():
            raise ValueError(f"host activation plan report missing required field: {field}")
    _assert_secret_free(report)


def _extract_step_commands(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("host activation plan steps must be lists.")
    commands: list[str] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("host activation plan steps must be mappings.")
        if item.get("execution_status") != "not_executed":
            raise ValueError("host activation plan steps must not have been executed.")
        command = str(item.get("command_preview", "")).strip()
        if not command:
            raise ValueError("host activation plan steps must include command_preview.")
        commands.append(command)
    if not commands:
        raise ValueError("host activation plan must include command previews.")
    return commands


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    for token in FORBIDDEN_EXECUTION_REQUEST_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("host activation execution request payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("host activation execution request payload must not reference repo-inside env files.")


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
