# Data Operations Scheduler Alert Boundary

Date: 2026-05-06

## Decision

`data-operations-scheduler-alert-boundary` adds a secret-free Prometheus-compatible alert rule reference for Data Operations scheduler health.

This task does not configure an Alertmanager receiver, Slack, email, PagerDuty, Opsgenie, webhook, or production Prometheus deployment.

## Rule File

```text
ops/observability/data-operations-alert-rules.yml
```

The validator is:

```bash
python3 scripts/validate_data_operations_alert_rules.py ops/observability/data-operations-alert-rules.yml
```

## Alerts

### DataOperationsJobMissing

Fires when a registered expected data operation has no latest observed run.

### DataOperationsJobFailed

Fires when the latest observed run for a registered data operation is failed.

### DataOperationsJobStale

Fires when a registered data operation exceeds its cadence stale threshold.

### DataOperationsRunTimeout

Fires when one or more artifact runner executions time out.

### DataOperationsArtifactMissing

Fires when stdout, stderr, or metadata artifacts expected from a data operation are missing.

### DataOperationsSchedulerPreflightFailure

Fires when the scheduler wrapper preflight fails before the child operation is run.

## Expected Metrics

- `data_operations_job_health_status`
- `data_operations_run_timeouts_total`
- `data_operations_artifact_missing_total`
- `data_operations_scheduler_preflight_failures_total`

These metrics are a reference boundary for the future data operations exporter or collector. The current task does not implement the exporter.

## Label Boundary

Allowed PromQL selector labels are bounded operational dimensions:

- `job`
- `job_id`
- `domain`
- `cadence`
- `pipeline_name`
- `health_status`
- `status`
- `reason`

Business identifiers such as ticker, symbol, portfolio name, document id, thesis id, recommendation id, request id, raw query, or database URL are forbidden.

## Receiver Boundary

Alertmanager receiver routing is intentionally absent.

Future receiver work must decide:

- destination type
- escalation policy
- on-call ownership
- mute windows
- secret storage location
- dry-run notification test

## Verification

Run:

```bash
bash scripts/verify_data_operations_scheduler_alert_boundary.sh
```

The verification checks the YAML shape, expected alert order, expected metrics, bounded selector labels, no receiver/secret tokens, docs markers, roadmap markers, and AWH.

## Not Implemented

- Alertmanager receiver routing.
- Slack/email/PagerDuty/Opsgenie/webhook configuration.
- Production Prometheus install.
- Data operations metric exporter.
- Actual scheduler activation.
- Provider network credential validation.
- DB schema changes.
- write APIs, RBAC, broker/order flow, benchmark/scoring/evaluation changes.

## Next Step

Next fixed task: `data-operations-scheduler-activation-runbook`.

That task should define the final manual activation gate, rollback, disable, and evidence checklist before any actual scheduler install or `launchctl bootstrap`.
