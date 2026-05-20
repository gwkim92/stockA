from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping


FORBIDDEN_MANUAL_HOST_PREFLIGHT_TOKENS = (
    "postgresql://",
    "api-key",
    "bearer ",
    "password",
)


def build_manual_host_scheduler_activation_preflight_report(
    *,
    manual_approval_report: Mapping[str, object],
    runtime_env_readiness_report: Mapping[str, object],
    manual_approval_report_path: str = "",
    runtime_env_readiness_report_path: str = "",
    generated_at: datetime | None = None,
) -> dict[str, object]:
    _validate_manual_approval_report(manual_approval_report)
    _assert_secret_free(runtime_env_readiness_report)

    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    exact_execution_commands = _as_string_list(manual_approval_report.get("exact_execution_commands"))
    exact_rollback_commands = _as_string_list(manual_approval_report.get("exact_rollback_commands"))
    runtime_status = str(runtime_env_readiness_report.get("runtime_env_readiness", ""))
    approval_gate = str(manual_approval_report.get("approval_gate", ""))
    base_report = {
        "report_name": "manual_host_scheduler_activation_preflight",
        "job_id": str(manual_approval_report["job_id"]),
        "pipeline_name": str(manual_approval_report.get("pipeline_name", "")),
        "domain": str(manual_approval_report.get("domain", "")),
        "cadence": str(manual_approval_report.get("cadence", "")),
        "rendered_label": str(manual_approval_report.get("rendered_label", "")),
        "host_plist_path_preview": str(manual_approval_report.get("host_plist_path_preview", "")),
        "manual_approval_report_path": manual_approval_report_path,
        "runtime_env_readiness_report_path": runtime_env_readiness_report_path,
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "host_activation_execution_performed": False,
        "codex_host_mutation_allowed": False,
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "exact_execution_commands": exact_execution_commands,
        "exact_rollback_commands": exact_rollback_commands,
        "secrets_policy": "manual_host_scheduler_activation_preflight_metadata_only_no_env_values",
    }

    if approval_gate != "approved_for_manual_operator_host_activation_not_executed_by_codex":
        report = {
            **base_report,
            "manual_activation_preflight": "blocked_manual_approval_not_ready",
            "manual_operator_may_execute_exact_commands": False,
            "approval_gate": approval_gate,
            "runtime_env_readiness": runtime_status,
            "required_next_step": "obtain_approved_manual_host_scheduler_activation_exact_command_packet",
            "manual_next_step": "manual-host-scheduler-activation-explicit-approval",
        }
        _assert_secret_free(report)
        return report

    if runtime_status != "passed":
        report = {
            **base_report,
            "manual_activation_preflight": "blocked_runtime_env_not_ready",
            "manual_operator_may_execute_exact_commands": False,
            "approval_gate": approval_gate,
            "runtime_env_readiness": runtime_status,
            "runtime_env_issues": list(runtime_env_readiness_report.get("issues", [])),
            "required_next_step": "fix_runtime_env_and_rerun_manual_host_scheduler_activation_preflight",
            "manual_next_step": "manual-host-scheduler-activation-preflight",
        }
        _assert_secret_free(report)
        return report

    report = {
        **base_report,
        "manual_activation_preflight": "passed_ready_for_external_manual_host_scheduler_activation",
        "manual_operator_may_execute_exact_commands": True,
        "approval_gate": approval_gate,
        "runtime_env_readiness": "passed",
        "operator_evidence_requirements": [
            "record_install_exit_status",
            "record_launchctl_bootstrap_exit_status",
            "record_launchctl_kickstart_exit_status",
            "capture_launchctl_print_output",
            "capture_first_run_artifact_directory",
            "capture_rollback_evidence_if_activation_fails",
        ],
        "required_next_step": "external_operator_runs_exact_commands_and_collects_evidence",
        "manual_next_step": "manual-host-scheduler-activation-operator-evidence",
    }
    _assert_secret_free(report)
    return report


def _validate_manual_approval_report(report: Mapping[str, object]) -> None:
    if report.get("report_name") != "manual_host_scheduler_activation_explicit_approval":
        raise ValueError("manual approval report has unexpected report_name.")
    if report.get("scheduler_activation") != "not_installed":
        raise ValueError("manual approval report must not install scheduler.")
    if report.get("launchctl_executed") is not False:
        raise ValueError("manual approval report must not execute launchctl.")
    if report.get("host_install_path_written") is not False:
        raise ValueError("manual approval report must not write host install path.")
    if report.get("child_command_executed") is not False:
        raise ValueError("manual approval report must not execute child command.")
    if report.get("host_activation_execution_performed") is not False:
        raise ValueError("manual approval report must not perform host activation execution.")
    if report.get("codex_host_mutation_allowed") is not False:
        raise ValueError("manual approval report must not allow Codex host mutation.")
    if not str(report.get("job_id", "")).strip():
        raise ValueError("manual approval report must include job_id.")
    if not _as_string_list(report.get("exact_execution_commands")):
        raise ValueError("manual approval report must include exact execution commands.")
    if not _as_string_list(report.get("exact_rollback_commands")):
        raise ValueError("manual approval report must include exact rollback commands.")
    _assert_secret_free(report)


def _as_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("command previews must be lists.")
    return [str(item) for item in value]


def _assert_secret_free(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False)
    lower_text = text.lower()
    for token in FORBIDDEN_MANUAL_HOST_PREFLIGHT_TOKENS:
        if token.lower() in lower_text:
            raise ValueError("manual host scheduler activation preflight payload contains secret-like value.")
    for value in _walk_values(payload):
        if isinstance(value, str) and _looks_like_repo_inside_env(value):
            raise ValueError("manual host scheduler activation preflight payload must not reference repo-inside env files.")


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
