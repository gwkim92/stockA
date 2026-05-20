# Implementation Plan

## Goal

Create a machine-readable approval gate for Data Operations scheduler activation.

## Steps

1. [x] Add `src/stockanalysis/operations/scheduler_activation_approval.py`.
2. [x] Add `tests/test_data_operations_scheduler_activation_approval.py`.
3. [x] Add `scripts/check_data_operations_scheduler_activation_approval_gate.sh`.
4. [x] Add `scripts/verify_data_operations_scheduler_activation_approval_gate.sh`.
5. [x] Add docs and update roadmap/README/verification/AGENTS.
6. [x] Update prior data-operations verification scripts for the new next task.
7. [x] Run targeted and full verification.

## Boundary

- The gate reads operator dry-run evidence.
- The gate optionally reads a repo-outside approval record.
- Missing approval record must block activation.
- Approved gate report still does not execute activation.
- Actual host scheduler mutation remains a future explicit approval task.

## Approval Record Shape

```json
{
  "approval_record": "data_operations_scheduler_activation_approval",
  "approval_decision": "approved",
  "operator": "operator-handle",
  "approved_at": "2026-05-11T12:00:00Z",
  "job_id": "macro-weekly",
  "operator_dry_run_report": "/repo-outside/evidence/operator-dry-run.json",
  "activation_window": "2026-05-11T12:00:00Z/2026-05-11T13:00:00Z",
  "rollback_owner": "operator-handle",
  "acknowledged_commands": [
    "install -m 600",
    "launchctl bootstrap",
    "launchctl kickstart",
    "launchctl print"
  ],
  "acknowledged_risks": [
    "host_scheduler_state_change",
    "recurring_data_operation_execution",
    "rollback_required_if_first_run_fails"
  ]
}
```
