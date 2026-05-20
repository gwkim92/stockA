# Implementation Plan

## Goal

Validate approve/deny execution decision records from a pending host activation execution request without executing host scheduler commands.

## Steps

1. [x] Add `src/stockanalysis/operations/scheduler_activation_execution_decision.py`.
2. [x] Add `tests/test_data_operations_scheduler_activation_execution_decision.py`.
3. [x] Add `scripts/decide_data_operations_live_scheduler_host_activation_execution.sh`.
4. [x] Add `scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh`.
5. [x] Add docs and update roadmap/README/verification/AGENTS.
6. [x] Update prior data-operations verification scripts for the new next task.
7. [x] Run targeted verification. Full verification is recorded in handoff/review after the final regression run.

## Boundary

- The decision may read an execution request report and an optional decision record.
- Approve may only move to final preflight.
- The decision must not run `launchctl`, write `~/Library/LaunchAgents`, or execute the child data operation command.
- Passing decision can only move to a future final preflight task.

## Output Shape

```json
{
  "report_name": "data_operations_live_scheduler_host_activation_execution_decision",
  "decision_gate": "approved_for_host_activation_execution_final_preflight",
  "user_decision": "approve_host_activation_execution",
  "host_activation_execution_allowed_in_this_task": false,
  "launchctl_executed": false,
  "manual_next_step": "data-operations-live-scheduler-host-activation-execution-final-preflight"
}
```
