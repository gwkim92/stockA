# Implementation Plan

## Goal

Create an operator dry-run flow that rehearses Data Operations scheduler activation without mutating host scheduler state.

## Steps

1. [x] Add `src/stockanalysis/operations/scheduler_operator_dry_run.py`.
2. [x] Add `tests/test_data_operations_scheduler_operator_dry_run.py`.
3. [x] Add `scripts/dry_run_data_operations_scheduler_operator_flow.sh`.
4. [x] Add `scripts/verify_data_operations_scheduler_operator_dry_run.sh`.
5. [x] Add docs and update roadmap/README/verification/AGENTS.
6. [x] Update prior data-operations verification scripts for the new next task.
7. [x] Run targeted and full verification.

## Boundary

- The dry-run may call `check_data_operations_runtime_env.sh`.
- The dry-run may call `run_data_operations_scheduler_job.sh --preflight-only`.
- The dry-run may call `render_data_operations_scheduler_install.sh`.
- The dry-run may call `validate_data_operations_alert_rules.py`.
- The dry-run must not run `launchctl`, write `~/Library/LaunchAgents`, or execute the child data operation command.

## Evidence

- `env-readiness.json`
- `scheduler-preflight.json`
- rendered `.plist`
- rendered `.manifest.json`
- `alert-rule-validation.txt`
- `operator-dry-run.json`
