# Implementation Plan

## Goal

Create a final preflight that validates approved activation evidence and fresh runtime env readiness without mutating host scheduler state.

## Steps

1. [x] Add `src/stockanalysis/operations/scheduler_activation_final_preflight.py`.
2. [x] Add `tests/test_data_operations_scheduler_activation_final_preflight.py`.
3. [x] Add `scripts/preflight_data_operations_live_scheduler_activation.sh`.
4. [x] Add `scripts/verify_data_operations_live_scheduler_activation_final_preflight.sh`.
5. [x] Add docs and update roadmap/README/verification/AGENTS.
6. [x] Update prior data-operations verification scripts for the new next task.
7. [x] Run targeted and full verification.

## Boundary

- The preflight may read activation decision, request, approval gate, and operator dry-run reports.
- The preflight may source a repo-outside env file to generate a fresh redacted runtime readiness report.
- The preflight must not run `launchctl`, write `~/Library/LaunchAgents`, or execute the child data operation command.
- Passing final preflight can only move to a host activation plan task, not execution.

## Output Shape

```json
{
  "report_name": "data_operations_live_scheduler_activation_final_preflight",
  "final_preflight": "passed_ready_for_host_activation_plan",
  "activation_allowed_for_host_activation_plan": true,
  "host_activation_execution_allowed_in_this_task": false,
  "launchctl_executed": false,
  "manual_next_step": "data-operations-live-scheduler-host-activation-plan"
}
```
