# Implementation Plan

## Goal

Create a Data Operations activation user-decision gate that validates explicit approve/deny decision records without mutating host scheduler state.

## Steps

1. [x] Add `src/stockanalysis/operations/scheduler_activation_decision.py`.
2. [x] Add `tests/test_data_operations_scheduler_activation_decision.py`.
3. [x] Add `scripts/decide_data_operations_live_scheduler_activation.sh`.
4. [x] Add `scripts/verify_data_operations_live_scheduler_activation_user_decision.sh`.
5. [x] Add docs and update roadmap/README/verification/AGENTS.
6. [x] Update prior data-operations verification scripts for the new next task.
7. [x] Run targeted and full verification.

## Boundary

- The gate may read a pending activation request report.
- The gate may read an explicit user decision record.
- Missing decision keeps activation blocked.
- Approve decision can only move to a future final preflight task.
- Deny decision stops the activation branch.
- The gate must not run `launchctl`, write `~/Library/LaunchAgents`, or execute the child data operation command.

## Decision Record Shape

```json
{
  "decision_record": "data_operations_live_scheduler_activation_user_decision",
  "decision": "approve_live_scheduler_activation",
  "decider": "operator-handle",
  "decided_at": "2026-05-11T12:30:00Z",
  "job_id": "macro-weekly",
  "activation_request_report": "/repo-outside/live-activation-request.json",
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
