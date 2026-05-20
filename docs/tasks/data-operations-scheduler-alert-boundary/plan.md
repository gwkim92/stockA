# Implementation Plan

## Goal

Create a secret-free alert rule boundary for Data Operations scheduler health before actual activation.

## Steps

1. [x] Add `ops/observability/data-operations-alert-rules.yml`.
2. [x] Add `scripts/validate_data_operations_alert_rules.py`.
3. [x] Add `scripts/verify_data_operations_scheduler_alert_boundary.sh`.
4. [x] Add docs and update roadmap/README/verification/AGENTS.
5. [x] Run targeted and full verification.

## Boundary

- Alert rules are Prometheus-compatible reference only.
- No receiver, webhook, token, route, Slack, email, PagerDuty, or Opsgenie config is included.
- Labels are bounded to static operational dimensions such as `job_id`, `domain`, `cadence`, `pipeline_name`, `health_status`, and `reason`.

## Metrics

- `data_operations_job_health_status`
- `data_operations_run_timeouts_total`
- `data_operations_artifact_missing_total`
- `data_operations_scheduler_preflight_failures_total`

## Alerts

- `DataOperationsJobMissing`
- `DataOperationsJobFailed`
- `DataOperationsJobStale`
- `DataOperationsRunTimeout`
- `DataOperationsArtifactMissing`
- `DataOperationsSchedulerPreflightFailure`
