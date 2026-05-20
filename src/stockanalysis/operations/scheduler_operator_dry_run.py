from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


def build_data_operations_scheduler_operator_dry_run_report(
    *,
    job_id: str,
    output_dir: str | Path,
    readiness_report: Mapping[str, object],
    preflight_report: Mapping[str, object],
    install_manifest: Mapping[str, object],
    alert_validation_output: str,
    evidence_paths: Mapping[str, str],
    generated_at: datetime | None = None,
) -> dict[str, object]:
    if not job_id:
        raise ValueError("job_id is required.")
    if not alert_validation_output.strip():
        raise ValueError("alert validation output is required.")

    _require(readiness_report.get("runtime_env_readiness") == "passed", "runtime env readiness must pass.")
    _require(preflight_report.get("preflight") == "passed", "scheduler preflight must pass.")
    _require(
        preflight_report.get("scheduler_activation") == "boundary_only_not_installed",
        "scheduler preflight must remain boundary-only.",
    )
    _require(install_manifest.get("install_mode") == "dry_run", "install manifest must be dry_run.")
    _require(install_manifest.get("scheduler_activation") == "not_installed", "scheduler must not be installed.")
    _require(install_manifest.get("host_install_path_written") is False, "host install path must not be written.")

    for report_name, payload in (
        ("readiness", readiness_report),
        ("preflight", preflight_report),
        ("install_manifest", install_manifest),
    ):
        _require(payload.get("job_id", job_id) == job_id, f"{report_name} job_id must match.")

    required_evidence = {
        "env_readiness_report",
        "scheduler_preflight_report",
        "install_manifest",
        "plist",
        "alert_validation_output",
    }
    missing = sorted(required_evidence - set(evidence_paths))
    if missing:
        raise ValueError(f"missing evidence paths: {', '.join(missing)}")

    generated_at_value = generated_at or datetime.now(timezone.utc)
    if generated_at_value.tzinfo is None:
        generated_at_value = generated_at_value.replace(tzinfo=timezone.utc)
    generated_at_value = generated_at_value.astimezone(timezone.utc).replace(microsecond=0)

    return {
        "report_name": "data_operations_scheduler_operator_dry_run",
        "operator_dry_run": "passed",
        "scheduler_activation": "not_installed",
        "host_install_path_written": False,
        "launchctl_executed": False,
        "child_command_executed": False,
        "requires_manual_approval": True,
        "job_id": job_id,
        "pipeline_name": preflight_report.get("pipeline_name") or install_manifest.get("pipeline_name", ""),
        "domain": preflight_report.get("domain") or install_manifest.get("domain", ""),
        "cadence": preflight_report.get("cadence") or install_manifest.get("cadence", ""),
        "output_dir": str(Path(output_dir)),
        "generated_at": generated_at_value.isoformat().replace("+00:00", "Z"),
        "checked_steps": [
            "runtime_env_readiness",
            "scheduler_preflight_only",
            "launchd_install_dry_run_render",
            "alert_rule_validation",
            "evidence_bundle_written",
        ],
        "evidence_paths": dict(evidence_paths),
        "validated_env_groups": list(readiness_report.get("validated_env_groups", [])),
        "rendered_label": str(install_manifest.get("label", "")),
        "rendered_scheduler_type": str(install_manifest.get("scheduler_type", "")),
        "manual_next_step": "data-operations-scheduler-activation-approval-gate",
        "secrets_policy": "values_redacted_env_names_only_no_env_values_in_report",
    }


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)
