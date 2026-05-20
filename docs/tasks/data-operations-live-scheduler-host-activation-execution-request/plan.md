# Implementation Plan

## Goal

Create an explicit execution approval request packet from a reviewed host activation plan without executing host scheduler commands.

## Steps

1. [x] Add `src/stockanalysis/operations/scheduler_activation_execution_request.py`.
2. [x] Add `tests/test_data_operations_scheduler_activation_execution_request.py`.
3. [x] Add `scripts/request_data_operations_live_scheduler_host_activation_execution.sh`.
4. [x] Add `scripts/verify_data_operations_live_scheduler_host_activation_execution_request.sh`.
5. [x] Add docs and update roadmap/README/verification/AGENTS.
6. [x] Update prior data-operations verification scripts for the new next task.
7. [x] Run targeted verification. Full verification is recorded in handoff/review after the final regression run.

## Boundary

- The request may read a host activation plan report.
- The request may copy install and `launchctl` command previews.
- The request must not run `launchctl`, write `~/Library/LaunchAgents`, or execute the child data operation command.
- Passing request can only move to a future explicit execution decision task.

## Output Shape

```json
{
  "report_name": "data_operations_live_scheduler_host_activation_execution_request",
  "execution_request": "pending_explicit_execution_approval",
  "requires_explicit_execution_approval": true,
  "host_activation_execution_allowed_in_this_task": false,
  "launchctl_executed": false,
  "manual_next_step": "data-operations-live-scheduler-host-activation-execution-decision"
}
```
