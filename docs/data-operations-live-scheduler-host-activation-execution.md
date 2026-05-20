# Data Operations Live Scheduler Host Activation Execution

Date: 2026-05-15

## Decision

`data-operations-live-scheduler-host-activation-execution` validates the final preflight output and an optional explicit host mutation confirmation record.

This task does not run `launchctl`, does not write `~/Library/LaunchAgents`, and does not execute child data operation commands.

## Interface

```bash
scripts/run_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-final-preflight-report /secure/path/execution-final-preflight.json \
  --output /secure/path/host-activation-execution.json
```

Optional confirmation:

```bash
scripts/run_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-final-preflight-report /secure/path/execution-final-preflight.json \
  --confirmation-record /secure/path/confirm-host-activation-execution.json \
  --output /secure/path/host-activation-execution.json
```

All input and output paths must be outside the repository.

## Outcomes

- `blocked_pending_explicit_host_mutation_confirmation`
- `aborted_by_explicit_host_mutation_confirmation`
- `confirmed_for_manual_host_mutation_not_executed_by_this_task`

Even the confirmed outcome keeps:

```json
{
  "host_activation_execution_allowed_in_this_task": false,
  "host_install_path_written": false,
  "launchctl_executed": false,
  "host_activation_execution_performed": false
}
```

## Confirmation Record Shape

```json
{
  "confirmation_record": "data_operations_live_scheduler_host_activation_execution_confirmation",
  "confirmation": "confirm_host_activation_execution",
  "confirmer": "operator-handle",
  "confirmed_at": "2026-05-15T09:00:00Z",
  "job_id": "macro-weekly",
  "execution_final_preflight_report": "/secure/path/execution-final-preflight.json",
  "confirmation_scope": "data_operations_scheduler_host_activation_execution",
  "acknowledged_final_preflight_state": "passed_ready_for_host_activation_execution_task",
  "acknowledged_mutation_boundary": [
    "host_launchagents_write",
    "launchctl_bootstrap",
    "launchctl_kickstart",
    "launchctl_print",
    "rollback_required_if_activation_fails",
    "recurring_data_operation_execution"
  ]
}
```

Use `abort_host_activation_execution` instead of `confirm_host_activation_execution` to explicitly block host mutation.

## Verification

Run:

```bash
bash scripts/verify_data_operations_live_scheduler_host_activation_execution.sh
```

The verification uses repo-outside final preflight evidence, checks missing/confirm/abort outcomes, rejects repo-inside paths and secret-like values, checks docs/roadmap markers, and runs AWH.

## Not Implemented

- Actual scheduler activation.
- `launchctl bootstrap`.
- Host LaunchAgents writes.
- Provider network credential validation.
- Alertmanager receiver routing.
- Production Prometheus install.
- DB schema changes.
- write APIs, RBAC, broker/order flow, benchmark/scoring/evaluation changes.

## Handoff Status

The next physical action is manual host scheduler activation or a future task with exact explicit user approval for the host commands. This task intentionally stops before that mutation.
