# Implementation Plan

## Goal

Create a Data Operations live scheduler activation request packet that is safe to show to the user before any host scheduler mutation.

## Steps

1. [x] Add `src/stockanalysis/operations/scheduler_activation_request.py`.
2. [x] Add `tests/test_data_operations_scheduler_activation_request.py`.
3. [x] Add `scripts/request_data_operations_live_scheduler_activation.sh`.
4. [x] Add `scripts/verify_data_operations_live_scheduler_activation_request.sh`.
5. [x] Add docs and update roadmap/README/verification/AGENTS.
6. [x] Update prior data-operations verification scripts for the new next task.
7. [x] Run targeted and full verification.

## Boundary

- The request may read approved approval gate evidence.
- The request may read operator dry-run evidence.
- The request may present command previews.
- The request must not run `launchctl`, write `~/Library/LaunchAgents`, or execute the child data operation command.
- The request must remain pending until the user explicitly approves or denies live activation.

## Request Output Shape

```json
{
  "report_name": "data_operations_live_scheduler_activation_request",
  "activation_request": "pending_explicit_user_approval",
  "requested_user_decision_values": [
    "approve_live_scheduler_activation",
    "deny_live_scheduler_activation"
  ],
  "launchctl_executed": false,
  "host_install_path_written": false,
  "manual_next_step": "data-operations-live-scheduler-activation-user-decision"
}
```
