# Data Operations Live Scheduler Host Activation Execution Decision

Date: 2026-05-11

## Decision

`data-operations-live-scheduler-host-activation-execution-decision` validates approve/deny decision records for a pending host activation execution request.

This task does not run `launchctl`, does not write to `~/Library/LaunchAgents`, and does not activate a scheduler.

## Interface

Missing decision:

```bash
scripts/decide_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-request-report /secure/path/host-activation-execution-request.json
```

Explicit decision:

```bash
scripts/decide_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-request-report /secure/path/host-activation-execution-request.json \
  --decision-record /secure/path/host-activation-execution-decision.json \
  --output /secure/path/host-activation-execution-decision-report.json
```

All input and output paths must be outside the repository.

## Decision Record Shape

```json
{
  "decision_record": "data_operations_live_scheduler_host_activation_execution_decision",
  "decision": "approve_host_activation_execution",
  "decider": "operator-handle",
  "decided_at": "2026-05-11T13:00:00Z",
  "job_id": "macro-weekly",
  "execution_request_report": "/secure/path/host-activation-execution-request.json",
  "decision_scope": "data_operations_scheduler_host_activation_execution",
  "acknowledged_request_state": "pending_explicit_execution_approval",
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

Allowed decisions:

- `approve_host_activation_execution`
- `deny_host_activation_execution`

## Gate Outcomes

Approve returns:

```json
{
  "decision_gate": "approved_for_host_activation_execution_final_preflight",
  "host_activation_execution_allowed_for_next_task": true,
  "host_activation_execution_allowed_in_this_task": false,
  "launchctl_executed": false
}
```

Deny returns:

```json
{
  "decision_gate": "denied_host_activation_execution",
  "host_activation_execution_allowed_for_next_task": false
}
```

Missing decision returns:

```json
{
  "decision_gate": "blocked_pending_execution_decision",
  "host_activation_execution_allowed_for_next_task": false
}
```

## Safety Boundary

- Execution request report and decision record must be outside the repository.
- Output path must be outside the repository.
- Approve only allows a future final preflight task.
- Raw env values, DB URLs, API keys, bearer tokens, and passwords are rejected from decision metadata.
- No script in this task runs `launchctl` or writes host LaunchAgents.

## Verification

Run:

```bash
bash scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh
```

The verification builds the repo-outside evidence chain, creates an execution request, validates missing/approve/deny decision reports, confirms fake secret values do not leak, refuses mismatched paths and repo-inside paths, checks docs/roadmap markers, and runs AWH.

## Not Implemented

- Actual scheduler activation.
- `launchctl bootstrap`.
- Host LaunchAgents writes.
- Final preflight immediately before execution.
- Provider network credential validation.
- Alertmanager receiver routing.
- Production Prometheus install.
- DB schema changes.
- write APIs, RBAC, broker/order flow, benchmark/scoring/evaluation changes.

## Next Step

Next fixed task: `data-operations-live-scheduler-host-activation-execution-final-preflight`.

That task should revalidate the approved execution decision, reviewed plan, and fresh runtime readiness immediately before any execution task. Actual host mutation remains forbidden until a later explicit execution task.
