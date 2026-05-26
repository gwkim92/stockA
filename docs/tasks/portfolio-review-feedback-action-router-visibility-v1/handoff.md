# portfolio-review-feedback-action-router-visibility-v1 Handoff

## Status

- completed: API/UI visibility for latest action-router artifacts is implemented, verified locally, deployed to EC2, and smoked against live data.

## Context

- The action router can now record `execute_feedback`, `execute_calibration`, or `no_op` audit artifacts.
- Current `/api/data-health` run history can show the pipeline succeeded, but it does not directly expose the action status, child runner, or guardrail reason as a first-class payload.

## Exact Next Step

- exact next step: continue the professional-analysis goal with the next quality/visibility task; do not change recommendation weights until outcome windows mature.

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
- `bash scripts/verify_project_execution_roadmap.sh`: passed.

## EC2 Evidence

- EC2 code commit deployed: `8eccd4f`.
- EC2 services after restart: `stockanalysis-frontend-api.service` active, `stockanalysis-web.service` active.
- EC2 compile/focused tests: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests && PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter`: 71 tests passed.
- EC2 Next build and roadmap verify: `npm --prefix apps/web run build && bash scripts/verify_project_execution_roadmap.sh`: passed.
- EC2 `/api/data-health`: `portfolio_review_feedback_action_router.status=loaded`, `eval_run_id=eval-run-35`, `source_cadence_eval_run_id=eval-run-34`, `action_status=no_op_wait_for_outcome_window`, `child_runner.executed=false`, `order_boundary=read_only_no_order`, `broker_submit_allowed=false`.
- EC2 `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25`: `risk_budget.review_feedback_action_router` returned the same loaded router state.
- EC2 route smoke: `/`, `/data-health`, and `/portfolio/coverage` returned HTTP `200`.
- EC2 text smoke: `/data-health` and `/portfolio/coverage` rendered `검토 실행 라우터`, `성과 관찰 기간 대기`, and `주문 경계`.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
