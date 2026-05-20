# Implementation Plan

## Goal

Create a host activation plan from final preflight evidence without executing host scheduler commands.

## Steps

1. [x] Add `src/stockanalysis/operations/scheduler_activation_host_plan.py`.
2. [x] Add `tests/test_data_operations_scheduler_activation_host_plan.py`.
3. [x] Add `scripts/plan_data_operations_live_scheduler_host_activation.sh`.
4. [x] Add `scripts/verify_data_operations_live_scheduler_host_activation_plan.sh`.
5. [x] Add docs and update roadmap/README/verification/AGENTS.
6. [x] Update prior data-operations verification scripts for the new next task.
7. [x] Run targeted verification. Full verification is recorded in handoff/review after the final regression run.

## Boundary

- The plan may read final preflight and activation request reports.
- The plan may include install and `launchctl` command previews.
- The plan must not run `launchctl`, write `~/Library/LaunchAgents`, or execute the child data operation command.
- Passing plan can only move to a future explicit execution request task.

## Output Shape

```json
{
  "report_name": "data_operations_live_scheduler_host_activation_plan",
  "host_activation_plan": "ready_for_execution_request",
  "activation_allowed_for_execution_request": true,
  "host_activation_execution_allowed_in_this_task": false,
  "launchctl_executed": false,
  "manual_next_step": "data-operations-live-scheduler-host-activation-execution-request"
}
```
