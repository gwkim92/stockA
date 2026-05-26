# portfolio-review-feedback-action-router-v1 Handoff

## Status

- completed: backend action-router runner, CLI command, cadence registry entry, decision-daily orchestrator step, and focused tests are implemented locally.
- EC2 deploy/smoke: completed on commit `6ffdca7`.

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

- exact next step: start `portfolio-review-feedback-action-router-visibility-v1` so the latest router decision is first-class API/UI state rather than only pipeline run history.

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

## EC2 Evidence

- EC2 commit: `6ffdca7`.
- Services: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active after restart.
- EC2 focused tests: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_portfolio_review_feedback_action_router tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator`: 107 tests passed.
- EC2 Next build: `npm --prefix apps/web run build` passed.
- EC2 roadmap verify: `bash scripts/verify_project_execution_roadmap.sh` passed.
- Runner: `stockanalysis-operations portfolio-review-feedback-action-router-run --portfolio-name "Long Term Paper" --as-of-date 2026-05-27 --execute` completed with `run_id=1638`, `eval_run_id=35`.
- Runner output: `source_cadence_eval_run_id=34`, `cadence_status=wait_for_outcome_window`, `route_action=no_op`, `action_status=no_op_wait_for_outcome_window`, `child_runner.executed=false`, `automatic_weight_change_allowed=false`, `automatic_rebalance_allowed=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- `/api/data-health`: pipeline `portfolio_review_feedback_action_router` shows `job_id=portfolio-review-feedback-action-router-daily`, `latest_status=succeeded`, `health_status=ok`, `latest_run_id=pipeline-run-1638`.
- Route smoke returned `200` for `/`, `/data-health`, and `/portfolio/coverage`.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
- Treat missing evidence and immature windows as no-op states.
