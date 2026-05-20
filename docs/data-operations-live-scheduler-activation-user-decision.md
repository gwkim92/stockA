# Data Operations Live Scheduler Activation User Decision

Date: 2026-05-11

## Decision

`data-operations-live-scheduler-activation-user-decision` validates an explicit user approve/deny decision record for a pending live scheduler activation request.

This task does not run `launchctl`, does not write to `~/Library/LaunchAgents`, and does not activate a scheduler.

## Interface

Pending without decision:

```bash
scripts/decide_data_operations_live_scheduler_activation.sh \
  --activation-request-report /secure/path/data-operations-live-activation-request.json
```

With explicit user decision:

```bash
scripts/decide_data_operations_live_scheduler_activation.sh \
  --activation-request-report /secure/path/data-operations-live-activation-request.json \
  --decision-record /secure/path/data-operations-live-activation-user-decision.json \
  --output /secure/path/data-operations-live-activation-decision-report.json
```

All input and output paths must be outside the repository.

## Decision Record Shape

```json
{
  "decision_record": "data_operations_live_scheduler_activation_user_decision",
  "decision": "approve_live_scheduler_activation",
  "decider": "operator-handle",
  "decided_at": "2026-05-11T12:30:00Z",
  "job_id": "macro-weekly",
  "activation_request_report": "/secure/path/data-operations-live-activation-request.json",
  "decision_scope": "data_operations_scheduler_host_activation",
  "acknowledged_request_state": "pending_explicit_user_approval",
  "acknowledged_mutation_boundary": [
    "host_launchagents_write",
    "launchctl_bootstrap",
    "recurring_data_operation_execution",
    "rollback_required_if_activation_fails"
  ]
}
```

## Gate Outcomes

No decision record returns:

```json
{
  "decision_gate": "blocked_pending_user_decision",
  "activation_allowed_for_next_task": false,
  "launchctl_executed": false
}
```

Valid approve decision returns:

```json
{
  "decision_gate": "approved_for_live_scheduler_activation_final_preflight",
  "activation_allowed_for_next_task": true,
  "activation_execution_allowed_in_this_task": false
}
```

Valid deny decision returns:

```json
{
  "decision_gate": "denied_live_scheduler_activation",
  "activation_allowed_for_next_task": false
}
```

## Safety Boundary

- Activation request report must be outside the repository.
- Decision record must be outside the repository.
- Decision output must be outside the repository when `--output` is used.
- Activation request must be `pending_explicit_user_approval`.
- Decision must be exactly `approve_live_scheduler_activation` or `deny_live_scheduler_activation`.
- Approve decision only allows a future final preflight task. It does not execute activation in this task.
- Raw env values, DB URLs, API keys, bearer tokens, and passwords are rejected from decision metadata.
- No script in this task runs `launchctl`.

## Verification

Run:

```bash
bash scripts/verify_data_operations_live_scheduler_activation_user_decision.sh
```

The verification generates repo-outside activation request evidence, checks blocked output without a decision, checks approve and deny decision outputs, confirms fake secret values do not leak, refuses repo-inside evidence paths, checks docs/roadmap markers, and runs AWH.

## Not Implemented

- Actual scheduler activation.
- `launchctl bootstrap`.
- Host LaunchAgents writes.
- Provider network credential validation.
- Alertmanager receiver routing.
- Production Prometheus install.
- DB schema changes.
- write APIs, RBAC, broker/order flow, benchmark/scoring/evaluation changes.

## Next Step

Completed next task: `data-operations-live-scheduler-activation-final-preflight`.

That task re-checks the latest request/decision evidence and runtime readiness. The next fixed task is `data-operations-live-scheduler-host-activation-plan`, which must prepare a host activation plan without executing it.
