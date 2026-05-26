# portfolio-review-feedback-action-router-v1 Handoff

## Status

- completed: backend action-router runner, CLI command, cadence registry entry, decision-daily orchestrator step, and focused tests are implemented locally.
- EC2 deploy/smoke remains pending after full local verification.

## Context

- The cadence task creates a persisted read-only `ai.eval_run` artifact with statuses:
  - `wait_for_outcome_window`
  - `run_feedback_now`
  - `run_calibration_now`
  - `missing_evidence_review_required`
  - `calibration_current`
- Current scheduler profiles can compute the cadence state, but they do not yet consume the status to run the appropriate safe follow-up runner.
- The action router now consumes the latest cadence artifact and executes at most one safe child runner:
  - `run_feedback_now` → `portfolio-review-decision-outcome-feedback-run`
  - `run_calibration_now` → `portfolio-review-feedback-calibration-run`
  - waiting/current/missing-evidence states → no-op audit artifact

## Exact Next Step

- exact next step: run full local verification, commit/push, deploy to EC2, run `portfolio-review-feedback-action-router-run --execute`, and confirm the router records a read-only audit artifact without changing weights or orders.

## Implemented

- Added `src/stockanalysis/operations/portfolio_review_feedback_action_router.py`.
- Added CLI command `portfolio-review-feedback-action-router-run`.
- Added daily cadence registry entry `portfolio-review-feedback-action-router-daily`.
- Added decision-daily/full-recovery orchestrator step `portfolio-review-feedback-action-router`.
- Added focused tests for missing cadence, wait no-op, feedback execution, calibration execution, guardrail blocking, SQL safety, and CLI wiring.

## Local Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`: passed.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_portfolio_review_feedback_action_router tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`: 107 tests passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: 1085 tests passed.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `bash scripts/verify_project_execution_roadmap.sh`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-review-feedback-action-router-v1`: passed.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
- Treat missing evidence and immature windows as no-op states.
