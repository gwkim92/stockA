from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


FORBIDDEN_FINAL_PREFLIGHT_TOKENS = (
    "postgresql://",
    "api-key",
    "bearer ",
    "password",
)


def build_data_operations_live_scheduler_activation_final_preflight_report(
    *,
    activation_decision_report: Mapping[str, object],
    activation_request_report: Mapping[str, object],
    approval_gate_report: Mapping[str, object],
    operator_dry_run_report: Mapping[str, object],
    runtime_env_readiness_report: Mapping[str, object],
    activation_decision_report_path: str = "",
    activation_request_report_path: str = "",
    approval_gate_report_path: str = "",
    operator_dry_run_report_path: str = "",
    runtime_env_readiness_report_path: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    _validate_decision_report(activation_decision_report, activation_request_report_path)
    _validate_activation_request_report(activation_request_report)
    _validate_approval_gate_report(approval_gate_report)
    _validate_operator_dry_run_report(operator_dry_run_report)
    _assert_secret_free(runtime_env_readiness_report)

    job_id = str(activation_request_report["job_id"])
    for label, report in (
        ("activation decision", activation_decision_report),
        ("approval gate", approval_gate_report),
        ("operator dry-run", operator_dry_run_report),
    ):
        if report.get("job_id") != job_id:
            raise ValueError(f"{label} report job_id must match activation request report.")

    _require_matching_path(
        actual=str(activation_request_report.get("approval_gate_report_path", "")),
        expected=approval_gate_report_path,
        label="approval gate report",
    )
    _require_matching_path(
        actual=str(activation_request_report.get("operator_dry_run_report_path", "")),
        expected=operator_dry_run_report_path,
        label="operator dry-run report",
    )

    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    base_report = {
        "report_name": "data_operations_live_scheduler_activation_final_preflight",
        "job_id": job_id,
        "pipeline_name": str(activation_request_report.get("pipeline_name", "")),
        "domain": str(activation_request_report.get("domain", "")),
        "cadence": str(activation_request_report.get("cadence", "")),
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_allowed_in_this_task": False,
        "activation_decision_report_path": activation_decision_report_path,
        "activation_request_report_path": activation_request_report_path,
        "approval_gate_report_path": approval_gate_report_path,
        "operator_dry_run_report_path": operator_dry_run_report_path,
        "runtime_env_readiness_report_path": runtime_env_readiness_report_path,
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "secrets_policy": "final_preflight_metadata_only_no_env_values",
    }

    if activation_decision_report.get("decision_gate") != "approved_for_live_scheduler_activation_final_preflight":
        report = {
            **base_report,
            "final_preflight": "blocked_user_decision_not_approved",
            "activation_allowed_for_host_activation_plan": False,
            "user_decision": str(activation_decision_report.get("user_decision", "")),
            "runtime_env_readiness": str(runtime_env_readiness_report.get("runtime_env_readiness", "")),
            "required_next_step": "obtain_approve_live_scheduler_activation_decision",
            "manual_next_step": "data-operations-live-scheduler-activation-user-decision",
        }
        _assert_secret_free(report)
        return report

    runtime_status = str(runtime_env_readiness_report.get("runtime_env_readiness", ""))
    if runtime_status != "passed":
        report = {
            **base_report,
            "final_preflight": "blocked_runtime_env_not_ready",
            "activation_allowed_for_host_activation_plan": False,
            "user_decision": "approve_live_scheduler_activation",
            "runtime_env_readiness": runtime_status,
            "runtime_env_issues": list(runtime_env_readiness_report.get("issues", [])),
            "required_next_step": "fix_runtime_env_and_rerun_final_preflight",
            "manual_next_step": "data-operations-live-scheduler-activation-final-preflight",
        }
        _assert_secret_free(report)
        return report

    report = {
        **base_report,
        "final_preflight": "passed_ready_for_host_activation_plan",
        "activation_allowed_for_host_activation_plan": True,
        "user_decision": "approve_live_scheduler_activation",
        "runtime_env_readiness": "passed",
        "checked_inputs": [
            "activation_decision_report",
            "activation_request_report",
            "activation_approval_gate_report",
            "operator_dry_run_report",
            "fresh_runtime_env_readiness_report",
        ],
        "required_next_step": "prepare_host_activation_plan_without_execution",
        "manual_next_step": "data-operations-live-scheduler-host-activation-plan",
    }
    _assert_secret_free(report)
    return report


def _validate_decision_report(report: Mapping[str, object], activation_request_report_path: str) -> None:
    if report.get("report_name") != "data_operations_live_scheduler_activation_user_decision":
        raise ValueError("activation decision report has unexpected report_name.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("activation decision report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("activation decision report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("activation decision report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("activation decision report must not execute child command.")
    if report.get("activation_execution_allowed_in_this_task") is not False:
        raise ValueError("activation decision report must not allow execution in that task.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("activation decision report must include job_id.")

    referenced_request = str(report.get("activation_request_report_path", "")).strip()
    if activation_request_report_path and referenced_request:
        _require_matching_path(
            actual=referenced_request,
            expected=activation_request_report_path,
            label="activation request report",
        )
    _assert_secret_free(report)


def _validate_activation_request_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_live_scheduler_activation_request":
        raise ValueError("activation request report has unexpected report_name.")
    if report.get("activation_request") != "pending_explicit_user_approval":
        raise ValueError("activation request report must be pending explicit user approval.")
    if report.get("activation_allowed_by_gate") is not True:
        raise ValueError("activation request report must be allowed by approval gate.")
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
    if not str(report.get("approval_gate_report_path", "")).strip():
        raise ValueError("activation request report must reference approval_gate_report_path.")
    if not str(report.get("operator_dry_run_report_path", "")).strip():
        raise ValueError("activation request report must reference operator_dry_run_report_path.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("activation request report must include job_id.")
    _assert_secret_free(report)


def _validate_approval_gate_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_scheduler_activation_approval_gate":
        raise ValueError("approval gate report has unexpected report_name.")
    if report.get("approval_gate") != "approved_for_manual_activation":
        raise ValueError("approval gate report must be approved_for_manual_activation.")
    if report.get("activation_allowed") is not True:
        raise ValueError("approval gate report must allow activation request.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("approval gate report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("approval gate report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("approval gate report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("approval gate report must not execute child command.")
    _assert_secret_free(report)


def _validate_operator_dry_run_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_scheduler_operator_dry_run":
        raise ValueError("operator dry-run report has unexpected report_name.")
    if report.get("operator_dry_run") != "passed":
        raise ValueError("operator dry-run report must be passed.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("operator dry-run report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("operator dry-run report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("operator dry-run report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("operator dry-run report must not execute child command.")
    if report.get("requires_manual_approval") is not True:
        raise ValueError("operator dry-run report must require manual approval.")
    _assert_secret_free(report)


def _require_matching_path(*, actual: str, expected: str, label: str) -> None:
    if actual and expected and _normalize_path(actual) != _normalize_path(expected):
        raise ValueError(f"{label} path must match referenced evidence.")


def _normalize_path(value: str) -> str:
    return str(Path(value).expanduser().resolve())


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    for token in FORBIDDEN_FINAL_PREFLIGHT_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("activation final preflight payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("activation final preflight payload must not reference repo-inside env files.")


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
