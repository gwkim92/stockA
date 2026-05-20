from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


FORBIDDEN_HOST_PLAN_TOKENS = (
    "postgresql://",
    "api-key",
    "bearer ",
    "password",
)


def build_data_operations_live_scheduler_host_activation_plan_report(
    *,
    final_preflight_report: Mapping[str, object],
    activation_request_report: Mapping[str, object],
    final_preflight_report_path: str = "",
    activation_request_report_path: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    _validate_final_preflight_report(final_preflight_report, activation_request_report_path)
    _validate_activation_request_report(activation_request_report)

    if final_preflight_report["job_id"] != activation_request_report["job_id"]:
        raise ValueError("final preflight and activation request job_id must match.")

    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    activation_commands = _as_string_list(activation_request_report.get("activation_command_preview"))
    rollback_commands = _as_string_list(activation_request_report.get("rollback_command_preview"))
    rendered_label = str(activation_request_report.get("rendered_label", "")).strip()
    host_plist_path = str(activation_request_report.get("host_plist_path_preview", "")).strip()
    if not rendered_label:
        raise ValueError("activation request report must include rendered_label.")
    if not host_plist_path:
        raise ValueError("activation request report must include host_plist_path_preview.")

    report = {
        "report_name": "data_operations_live_scheduler_host_activation_plan",
        "host_activation_plan": "ready_for_execution_request",
        "activation_allowed_for_execution_request": True,
        "host_activation_execution_allowed_in_this_task": False,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "job_id": str(final_preflight_report["job_id"]),
        "pipeline_name": str(final_preflight_report.get("pipeline_name", "")),
        "domain": str(final_preflight_report.get("domain", "")),
        "cadence": str(final_preflight_report.get("cadence", "")),
        "rendered_label": rendered_label,
        "host_plist_path_preview": host_plist_path,
        "final_preflight_report_path": final_preflight_report_path,
        "activation_request_report_path": activation_request_report_path,
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "pre_execution_checks": [
            "confirm_final_preflight_report_is_current",
            "confirm_user_execution_request_is_created_after_this_plan",
            "confirm_no_existing_launchd_label_conflict",
            "confirm_rollback_owner_is_available",
            "confirm_observability_alerts_are_reachable",
        ],
        "execution_plan_steps": _build_step_plan(activation_commands),
        "rollback_plan_steps": _build_step_plan(rollback_commands),
        "operator_warnings": [
            "This plan is not execution approval.",
            "Do not run command previews until a later explicit execution task approves host mutation.",
            "Re-run final preflight if env, evidence, scheduler files, or operator context changed.",
        ],
        "required_next_step": "request_explicit_host_activation_execution_approval",
        "manual_next_step": "data-operations-live-scheduler-host-activation-execution-request",
        "secrets_policy": "host_activation_plan_metadata_only_no_env_values",
    }
    _assert_secret_free(report)
    return report


def render_data_operations_live_scheduler_host_activation_plan_markdown(report: Mapping[str, object]) -> str:
    _assert_secret_free(report)
    lines = [
        "# Data Operations Host Activation Plan",
        "",
        f"- job_id: `{report.get('job_id', '')}`",
        f"- label: `{report.get('rendered_label', '')}`",
        f"- host plist preview: `{report.get('host_plist_path_preview', '')}`",
        f"- execution allowed in this task: `{str(report.get('host_activation_execution_allowed_in_this_task')).lower()}`",
        "",
        "## Pre-Execution Checks",
    ]
    for item in report.get("pre_execution_checks", []):
        lines.append(f"- {item}")

    lines.extend(["", "## Command Preview"])
    for step in report.get("execution_plan_steps", []):
        if isinstance(step, Mapping):
            lines.append(f"{step.get('order')}. `{step.get('command_preview', '')}`")

    lines.extend(["", "## Rollback Preview"])
    for step in report.get("rollback_plan_steps", []):
        if isinstance(step, Mapping):
            lines.append(f"{step.get('order')}. `{step.get('command_preview', '')}`")

    lines.extend(
        [
            "",
            "## Boundary",
            "- This document is a plan only.",
            "- It must not be treated as execution approval.",
            "- Next task: `data-operations-live-scheduler-host-activation-execution-request`.",
            "",
        ]
    )
    return "\n".join(lines)


def _validate_final_preflight_report(report: Mapping[str, object], activation_request_report_path: str) -> None:
    if report.get("report_name") != "data_operations_live_scheduler_activation_final_preflight":
        raise ValueError("final preflight report has unexpected report_name.")
    if report.get("final_preflight") != "passed_ready_for_host_activation_plan":
        raise ValueError("final preflight report must be passed_ready_for_host_activation_plan.")
    if report.get("activation_allowed_for_host_activation_plan") is not True:
        raise ValueError("final preflight report must allow host activation planning.")
    if report.get("host_activation_execution_allowed_in_this_task") is not False:
        raise ValueError("final preflight report must not allow host activation execution in that task.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("final preflight report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("final preflight report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("final preflight report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("final preflight report must not execute child command.")
    if report.get("manual_next_step") != "data-operations-live-scheduler-host-activation-plan":
        raise ValueError("final preflight report must point to the host activation plan task.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("final preflight report must include job_id.")

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
        raise ValueError("activation request report must remain pending explicit user approval.")
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
    if not _as_string_list(report.get("activation_command_preview")):
        raise ValueError("activation request report must include activation command previews.")
    if not _as_string_list(report.get("rollback_command_preview")):
        raise ValueError("activation request report must include rollback command previews.")
    _assert_secret_free(report)


def _build_step_plan(commands: list[str]) -> list[dict[str, object]]:
    return [
        {
            "order": index,
            "command_preview": command,
            "execution_status": "not_executed",
        }
        for index, command in enumerate(commands, start=1)
    ]


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
    for token in FORBIDDEN_HOST_PLAN_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("host activation plan payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("host activation plan payload must not reference repo-inside env files.")


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
