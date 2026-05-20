from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping

from stockanalysis.operations.scheduler_activation_approval import (
    REQUIRED_APPROVAL_COMMANDS,
    REQUIRED_RISK_ACKNOWLEDGEMENTS,
)


FORBIDDEN_ACTIVATION_REQUEST_TOKENS = (
    "postgresql://",
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "FRED_API_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "api-key",
    "bearer ",
    "password",
)


def build_data_operations_live_scheduler_activation_request_report(
    *,
    approval_gate_report: Mapping[str, object],
    operator_dry_run_report: Mapping[str, object],
    approval_gate_report_path: str = "",
    operator_dry_run_report_path: str = "",
    request_note: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    """Create an explicit user approval request without activating launchd."""

    _validate_approval_gate_report(approval_gate_report)
    _validate_operator_dry_run_report(operator_dry_run_report)
    if approval_gate_report["job_id"] != operator_dry_run_report["job_id"]:
        raise ValueError("approval gate and operator dry-run job_id must match.")

    gate_operator_report_path = str(approval_gate_report.get("operator_dry_run_report_path", "")).strip()
    if operator_dry_run_report_path and gate_operator_report_path:
        if _normalize_path(operator_dry_run_report_path) != _normalize_path(gate_operator_report_path):
            raise ValueError("operator dry-run report path must match approval gate evidence.")

    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    evidence_paths = operator_dry_run_report.get("evidence_paths")
    if not isinstance(evidence_paths, Mapping):
        raise ValueError("operator dry-run report evidence_paths must be a mapping.")

    label = str(operator_dry_run_report.get("rendered_label", "")).strip()
    if not label:
        raise ValueError("operator dry-run report must include rendered_label.")

    plist_source_path = str(evidence_paths.get("plist", "")).strip()
    host_plist_path = f"$HOME/Library/LaunchAgents/{label}.plist"
    activation_command_preview = [
        f'install -m 600 "{plist_source_path}" "{host_plist_path}"',
        f'launchctl bootstrap "gui/$(id -u)" "{host_plist_path}"',
        f'launchctl kickstart -k "gui/$(id -u)/{label}"',
        f'launchctl print "gui/$(id -u)/{label}"',
    ]
    rollback_command_preview = [
        f'launchctl bootout "gui/$(id -u)" "{host_plist_path}"',
        f'rm -f "{host_plist_path}"',
    ]

    report = {
        "report_name": "data_operations_live_scheduler_activation_request",
        "activation_request": "pending_explicit_user_approval",
        "requested_user_decision_values": [
            "approve_live_scheduler_activation",
            "deny_live_scheduler_activation",
        ],
        "required_user_action": "reply_with_approve_live_scheduler_activation_or_deny_live_scheduler_activation",
        "requires_explicit_user_approval": True,
        "activation_allowed_by_gate": True,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "job_id": str(approval_gate_report["job_id"]),
        "pipeline_name": str(approval_gate_report.get("pipeline_name", "")),
        "domain": str(approval_gate_report.get("domain", "")),
        "cadence": str(approval_gate_report.get("cadence", "")),
        "operator": str(approval_gate_report["operator"]),
        "approved_at": str(approval_gate_report["approved_at"]),
        "approval_gate_report_path": approval_gate_report_path,
        "operator_dry_run_report_path": operator_dry_run_report_path or gate_operator_report_path,
        "approval_record_path": str(approval_gate_report.get("approval_record_path", "")),
        "activation_window": str(approval_gate_report["activation_window"]),
        "rollback_owner": str(approval_gate_report["rollback_owner"]),
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "request_note": request_note,
        "rendered_label": label,
        "rendered_scheduler_type": str(operator_dry_run_report.get("rendered_scheduler_type", "")),
        "host_plist_path_preview": host_plist_path,
        "activation_command_preview": activation_command_preview,
        "rollback_command_preview": rollback_command_preview,
        "evidence_summary": {
            "approval_gate_report": approval_gate_report_path,
            "operator_dry_run_report": operator_dry_run_report_path or gate_operator_report_path,
            "env_readiness_report": str(evidence_paths.get("env_readiness_report", "")),
            "scheduler_preflight_report": str(evidence_paths.get("scheduler_preflight_report", "")),
            "install_manifest": str(evidence_paths.get("install_manifest", "")),
            "plist": plist_source_path,
            "alert_validation_output": str(evidence_paths.get("alert_validation_output", "")),
            "approval_record": str(approval_gate_report.get("approval_record_path", "")),
        },
        "safety_boundary": {
            "writes_host_launchagents": False,
            "executes_launchctl": False,
            "executes_child_command": False,
            "requires_separate_user_decision_record": True,
        },
        "manual_next_step": "data-operations-live-scheduler-activation-user-decision",
        "secrets_policy": "activation_request_metadata_only_no_env_values",
    }
    _assert_secret_free(report)
    return report


def _validate_approval_gate_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_scheduler_activation_approval_gate":
        raise ValueError("approval gate report has unexpected report_name.")
    if report.get("approval_gate") != "approved_for_manual_activation":
        raise ValueError("approval gate report must be approved_for_manual_activation.")
    if report.get("activation_allowed") is not True:
        raise ValueError("approval gate report must allow manual activation request.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("approval gate report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("approval gate report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("approval gate report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("approval gate report must not execute child command.")
    if report.get("manual_next_step") != "data-operations-live-scheduler-activation-request":
        raise ValueError("approval gate report must point to the activation request task.")

    for field in ("job_id", "operator", "approved_at", "activation_window", "rollback_owner"):
        if not str(report.get(field, "")).strip():
            raise ValueError(f"approval gate report missing required field: {field}")

    acknowledged_commands = {str(item) for item in _as_list(report.get("acknowledged_commands"))}
    missing_commands = sorted(REQUIRED_APPROVAL_COMMANDS - acknowledged_commands)
    if missing_commands:
        raise ValueError(f"approval gate report missing acknowledged commands: {', '.join(missing_commands)}")

    acknowledged_risks = {str(item) for item in _as_list(report.get("acknowledged_risks"))}
    missing_risks = sorted(REQUIRED_RISK_ACKNOWLEDGEMENTS - acknowledged_risks)
    if missing_risks:
        raise ValueError(f"approval gate report missing risk acknowledgements: {', '.join(missing_risks)}")

    _assert_secret_free(report)


def _validate_operator_dry_run_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "data_operations_scheduler_operator_dry_run":
        raise ValueError("operator dry-run report has unexpected report_name.")
    if report.get("operator_dry_run") != "passed":
        raise ValueError("operator dry-run report must be passed.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("operator dry-run must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("operator dry-run must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("operator dry-run must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("operator dry-run must not execute child command.")
    if report.get("requires_manual_approval") is not True:
        raise ValueError("operator dry-run must require manual approval.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("operator dry-run report must include job_id.")

    evidence_paths = report.get("evidence_paths")
    if not isinstance(evidence_paths, Mapping):
        raise ValueError("operator dry-run report evidence_paths must be a mapping.")
    required_evidence = {
        "env_readiness_report",
        "scheduler_preflight_report",
        "install_manifest",
        "plist",
        "alert_validation_output",
    }
    missing = sorted(required_evidence - set(evidence_paths))
    if missing:
        raise ValueError(f"operator dry-run report missing evidence paths: {', '.join(missing)}")

    _assert_secret_free(report)


def _as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("approval acknowledgement fields must be lists.")
    return value


def _normalize_path(value: str) -> str:
    return str(Path(value).expanduser().resolve())


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    for token in FORBIDDEN_ACTIVATION_REQUEST_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("activation request payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("activation request payload must not reference repo-inside env files.")


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
