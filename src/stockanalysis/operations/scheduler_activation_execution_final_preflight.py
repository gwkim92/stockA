from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


FORBIDDEN_EXECUTION_FINAL_PREFLIGHT_TOKENS = (
    "postgresql://",
    "api-key",
    "bearer ",
    "password",
)


def build_data_operations_live_scheduler_host_activation_execution_final_preflight_report(
    *,
    execution_decision_report: Mapping[str, object],
    execution_request_report: Mapping[str, object],
    host_activation_plan_report: Mapping[str, object],
    runtime_env_readiness_report: Mapping[str, object],
    execution_decision_report_path: str = "",
    execution_request_report_path: str = "",
    host_activation_plan_report_path: str = "",
    runtime_env_readiness_report_path: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    _validate_execution_decision_report(execution_decision_report, execution_request_report_path)
    _validate_execution_request_report(execution_request_report, host_activation_plan_report_path)
    _validate_host_activation_plan_report(host_activation_plan_report)
    _assert_secret_free(runtime_env_readiness_report)

    job_id = str(execution_request_report["job_id"])
    for label, report in (
        ("execution decision", execution_decision_report),
        ("host activation plan", host_activation_plan_report),
    ):
        if report.get("job_id") != job_id:
            raise ValueError(f"{label} report job_id must match execution request report.")

    plan_commands = _extract_step_commands(host_activation_plan_report.get("execution_plan_steps"))
    request_commands = _as_string_list(execution_request_report.get("execution_command_preview"))
    if plan_commands != request_commands:
        raise ValueError("execution request command preview must match reviewed host activation plan.")

    plan_rollback_commands = _extract_step_commands(host_activation_plan_report.get("rollback_plan_steps"))
    request_rollback_commands = _as_string_list(execution_request_report.get("rollback_command_preview"))
    if plan_rollback_commands != request_rollback_commands:
        raise ValueError("execution request rollback preview must match reviewed host activation plan.")

    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    base_report = {
        "report_name": "data_operations_live_scheduler_host_activation_execution_final_preflight",
        "job_id": job_id,
        "pipeline_name": str(execution_request_report.get("pipeline_name", "")),
        "domain": str(execution_request_report.get("domain", "")),
        "cadence": str(execution_request_report.get("cadence", "")),
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_allowed_in_this_task": False,
        "execution_decision_report_path": execution_decision_report_path,
        "execution_request_report_path": execution_request_report_path,
        "host_activation_plan_report_path": host_activation_plan_report_path,
        "runtime_env_readiness_report_path": runtime_env_readiness_report_path,
        "rendered_label": str(execution_request_report.get("rendered_label", "")),
        "host_plist_path_preview": str(execution_request_report.get("host_plist_path_preview", "")),
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "secrets_policy": "host_activation_execution_final_preflight_metadata_only_no_env_values",
    }

    if execution_decision_report.get("decision_gate") != "approved_for_host_activation_execution_final_preflight":
        report = {
            **base_report,
            "execution_final_preflight": "blocked_execution_decision_not_approved",
            "host_activation_execution_allowed_for_next_task": False,
            "user_decision": str(execution_decision_report.get("user_decision", "")),
            "runtime_env_readiness": str(runtime_env_readiness_report.get("runtime_env_readiness", "")),
            "required_next_step": "obtain_approve_host_activation_execution_decision",
            "manual_next_step": "data-operations-live-scheduler-host-activation-execution-decision",
        }
        _assert_secret_free(report)
        return report

    runtime_status = str(runtime_env_readiness_report.get("runtime_env_readiness", ""))
    if runtime_status != "passed":
        report = {
            **base_report,
            "execution_final_preflight": "blocked_runtime_env_not_ready",
            "host_activation_execution_allowed_for_next_task": False,
            "user_decision": "approve_host_activation_execution",
            "runtime_env_readiness": runtime_status,
            "runtime_env_issues": list(runtime_env_readiness_report.get("issues", [])),
            "required_next_step": "fix_runtime_env_and_rerun_host_activation_execution_final_preflight",
            "manual_next_step": "data-operations-live-scheduler-host-activation-execution-final-preflight",
        }
        _assert_secret_free(report)
        return report

    report = {
        **base_report,
        "execution_final_preflight": "passed_ready_for_host_activation_execution_task",
        "host_activation_execution_allowed_for_next_task": True,
        "user_decision": "approve_host_activation_execution",
        "runtime_env_readiness": "passed",
        "checked_inputs": [
            "host_activation_execution_decision_report",
            "host_activation_execution_request_report",
            "reviewed_host_activation_plan_report",
            "fresh_runtime_env_readiness_report",
        ],
        "execution_command_preview": request_commands,
        "rollback_command_preview": request_rollback_commands,
        "required_next_step": "run_separate_host_activation_execution_task_with_explicit_user_confirmation",
        "manual_next_step": "data-operations-live-scheduler-host-activation-execution",
    }
    _assert_secret_free(report)
    return report


def _validate_execution_decision_report(report: Mapping[str, object], execution_request_report_path: str) -> None:
    if report.get("report_name") != "data_operations_live_scheduler_host_activation_execution_decision":
        raise ValueError("execution decision report has unexpected report_name.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("execution decision report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("execution decision report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("execution decision report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("execution decision report must not execute child command.")
    if report.get("host_activation_execution_allowed_in_this_task") is not False:
        raise ValueError("execution decision report must not allow execution in that task.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("execution decision report must include job_id.")

    referenced_request = str(report.get("execution_request_report_path", "")).strip()
    if execution_request_report_path and referenced_request:
        _require_matching_path(
            actual=referenced_request,
            expected=execution_request_report_path,
            label="execution request report",
        )
    _assert_secret_free(report)


def _validate_execution_request_report(report: Mapping[str, object], host_activation_plan_report_path: str) -> None:
    if report.get("report_name") != "data_operations_live_scheduler_host_activation_execution_request":
        raise ValueError("execution request report has unexpected report_name.")
    if report.get("execution_request") != "pending_explicit_execution_approval":
        raise ValueError("execution request report must be pending_explicit_execution_approval.")
    if report.get("requires_explicit_execution_approval") is not True:
        raise ValueError("execution request report must require explicit execution approval.")
    if report.get("execution_allowed_by_plan") is not True:
        raise ValueError("execution request report must be allowed by plan.")
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

    referenced_plan = str(report.get("host_activation_plan_report_path", "")).strip()
    if host_activation_plan_report_path and referenced_plan:
        _require_matching_path(
            actual=referenced_plan,
            expected=host_activation_plan_report_path,
            label="host activation plan report",
        )
    if not _as_string_list(report.get("execution_command_preview")):
        raise ValueError("execution request report must include execution command previews.")
    if not _as_string_list(report.get("rollback_command_preview")):
        raise ValueError("execution request report must include rollback command previews.")
    _assert_secret_free(report)


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
    if not _extract_step_commands(report.get("execution_plan_steps")):
        raise ValueError("host activation plan report must include execution plan steps.")
    if not _extract_step_commands(report.get("rollback_plan_steps")):
        raise ValueError("host activation plan report must include rollback plan steps.")
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


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("command previews must be lists.")
    return [str(item) for item in value]


def _require_matching_path(*, actual: str, expected: str, label: str) -> None:
    if actual and expected and _normalize_path(actual) != _normalize_path(expected):
        raise ValueError(f"{label} path must match referenced evidence.")


def _normalize_path(value: str) -> str:
    return str(Path(value).expanduser().resolve())


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    for token in FORBIDDEN_EXECUTION_FINAL_PREFLIGHT_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("host activation execution final preflight payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("host activation execution final preflight payload must not reference repo-inside env files.")


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
