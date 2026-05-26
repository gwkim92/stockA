# portfolio-review-feedback-action-router-visibility-v1 Handoff

## Status

- implemented locally: API/UI visibility for latest action-router artifacts is wired and verified locally.
- EC2 deploy/smoke: pending.

## Context

- The action router can now record `execute_feedback`, `execute_calibration`, or `no_op` audit artifacts.
- Current `/api/data-health` run history can show the pipeline succeeded, but it does not directly expose the action status, child runner, or guardrail reason as a first-class payload.

## Exact Next Step

- exact next step: run roadmap/AWH verification, then commit/push and deploy to EC2 for live API/route smoke.

## Implemented

- Added read-only live adapter lookup for latest `portfolio_review_feedback_action_router` `ai.eval_run`.
- Added `/api/data-health` payload `portfolio_review_feedback_action_router`.
- Added portfolio coverage payload `risk_budget.review_feedback_action_router`.
- Added Korean UI sections on `/data-health` and `/portfolio/coverage` showing:
  - source cadence artifact
  - route action
  - action status
  - child runner execution status
  - guardrail/order boundary
  - next action
- Added frontend contract types and focused live adapter assertions.

## Local Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`: passed.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`: 71 tests passed.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: 1086 tests passed.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
