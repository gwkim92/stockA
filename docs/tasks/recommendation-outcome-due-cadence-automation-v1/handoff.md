# recommendation-outcome-due-cadence-automation-v1 Handoff

## Status

- completed: implemented, pushed, deployed to EC2, and smoked against the live DB.

## Context

- EC2 maturity monitor reports `status=not_due`, `next_due_date=2026-06-20`, `next_due_count=19`.
- `recommendation_weight_review_readiness` remains `blocked_by_outcome_calibration_no_due_outcome_window`.
- The monitor is visible, but scheduler/cadence still needs to use it as an operational trigger.

## Exact Next Step

- exact next step: move to `professional-source-gap-prioritization-v1` so the remaining professional analysis blockers are ranked by impact and remediation action.

## Implementation Evidence

- implementation commit: `bf44aae` (`Add outcome maturity cadence action`).
- `/api/data-health` now includes `recommendation_outcome_maturity.cadence_action`.
- `due_outcomes_ready` and `overdue_outcomes_ready` return `run_outcome_calibration_now` with the `recommendation-outcome-calibration-sample-expansion-run` command.
- `blocked_by_price_gaps` returns `repair_price_history_then_calibrate` with a market price refresh command and calibration follow-up command.
- `not_due` returns `wait_until_next_due_date` with the next due date and a future calibration command.
- `/data-health` now renders `실행 액션` inside the recommendation outcome section.
- The action payload always keeps `automatic_weight_change_allowed=false`, `automatic_order_allowed=false`, and `broker_submit_allowed=false`.

## Verification Evidence

- local passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- local passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- local passed: `cd apps/web && npm run typecheck`
- local passed: `cd apps/web && npm run build`
- EC2 deployed commit: `bf44aae`
- EC2 passed: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- EC2 passed: `cd apps/web && npm run typecheck && npm run build`
- EC2 services active: `stockanalysis-frontend-api.service`, `stockanalysis-web.service`.
- EC2 `/api/data-health` result: `maturity_status=not_due`, `next_due_date=2026-06-20`, `next_due_count=19`, `action_status=wait_until_next_due_date`, `action_type=wait`, `should_run_now=false`, `should_wait=true`, `wait_until=2026-06-20`, command `stockanalysis-operations recommendation-outcome-calibration-sample-expansion-run --env-file <ENV> --as-of-date 2026-06-20 --execute`, `blocks_weight_review=true`, `automatic_weight_change_allowed=false`.
- EC2 `/data-health` renders `실행 액션`, `다음 측정일까지 대기`, `성과 측정창`, and `다음 측정일`.
- local browser tunnel `http://127.0.0.1:13000/data-health` returned HTTP 200.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate outcomes.
- Do not treat `not_due` as a failure.
