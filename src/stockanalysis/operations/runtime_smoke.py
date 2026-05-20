from __future__ import annotations

import json
from typing import Mapping


def build_data_operations_runtime_smoke_report(
    *,
    readiness_report: Mapping[str, object],
    artifact_run: Mapping[str, object],
) -> dict[str, object]:
    readiness_status = readiness_report.get("runtime_env_readiness")
    if readiness_status != "passed":
        raise ValueError("Data operations runtime smoke requires passed env readiness.")

    artifact_status = artifact_run.get("status")
    exit_code = int(artifact_run.get("exit_code", 1))
    smoke_status = "passed" if artifact_status == "succeeded" and exit_code == 0 else "failed"

    report = {
        "report_name": "data_operations_runtime_smoke",
        "runtime_smoke": smoke_status,
        "runtime_env_readiness": readiness_status,
        "job_id": artifact_run.get("job_id", ""),
        "pipeline_name": artifact_run.get("pipeline_name", ""),
        "domain": artifact_run.get("domain", ""),
        "cadence": artifact_run.get("cadence", ""),
        "artifact_run_status": artifact_status,
        "exit_code": exit_code,
        "artifact_dir": artifact_run.get("artifact_dir", ""),
        "metadata_path": artifact_run.get("metadata_path", ""),
        "stdout_path": artifact_run.get("stdout_path", ""),
        "stdout_json_path": artifact_run.get("stdout_json_path", ""),
        "stderr_path": artifact_run.get("stderr_path", ""),
        "stdout_format": artifact_run.get("stdout_format", ""),
        "duration_ms": artifact_run.get("duration_ms", 0),
        "validated_env_groups": list(readiness_report.get("validated_env_groups", [])),
        "cadence_required_env_groups": list(readiness_report.get("cadence_required_env_groups", [])),
        "secrets_policy": "values_redacted_env_names_only",
        "scheduler_activation": "not_activated",
    }
    _assert_secret_free_payload(report)
    if smoke_status != "passed":
        raise ValueError(f"Data operations runtime smoke failed for job_id={report['job_id']!r}.")
    return report


def _assert_secret_free_payload(payload: Mapping[str, object]) -> None:
    text = json.dumps(payload, sort_keys=True)
    forbidden_markers = (
        "://runtime_user:",
        "postgresql://",
        "postgres://",
        "fred-runtime-token",
        "alpha-runtime-token",
        "openai-runtime-key",
        "contact@operator",
        "USER:PASSWORD",
    )
    for marker in forbidden_markers:
        if marker in text:
            raise ValueError("Runtime smoke report contains a secret-like value.")
