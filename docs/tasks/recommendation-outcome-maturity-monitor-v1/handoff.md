# recommendation-outcome-maturity-monitor-v1 Handoff

## Status

- completed: implemented, pushed, deployed to EC2, and smoked against the live DB.

## Context

- EC2 `recommendation-weight-review-readiness-audit-run` on commit `b3e2915` produced `run_id=1598`, `audit_eval_run_id=28`.
- The source quality eval was `ready_for_weight_review`, but the horizon-grid calibration gate was `no_due_outcome_window`.
- Current measured state: `recommendation_horizon_count=180`, `recommendation_count=45`, `outcome_count=0`, `not_due=180`.
- Therefore the next useful work is not weight tuning. It is making the waiting period operationally visible and automatically actionable when outcomes become due.

## Exact Next Step

- exact next step: move to `recommendation-outcome-due-cadence-automation-v1` so the scheduler/cadence layer reruns outcome calibration when maturity monitor reports due or overdue windows.

## Implementation Evidence

- implementation commit: `83f750c` (`Expose recommendation outcome maturity monitor`).
- `/api/data-health` now includes `recommendation_outcome_maturity`.
- The monitor is a read-only projection over active recommendations, latest calibration horizon days, price bars, and existing `performance.recommendation_outcome`.
- It exposes `status`, `next_due_date`, `next_due_count`, `not_due_count`, `ready_for_backfill_count`, `due_today_count`, `overdue_count`, `price_gap_count`, price-gap breakdown, example rows, and the source calibration eval id.
- `/data-health` now renders `성과 측정창`, `다음 측정일`, and `지연/가격 보강` next to recommendation outcome calibration.

## Verification Evidence

- local passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- local passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- local passed: `cd apps/web && npm run typecheck`
- local passed: `cd apps/web && npm run build`
- EC2 deployed commit: `83f750c`
- EC2 passed: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- EC2 passed: `cd apps/web && npm run typecheck && npm run build`
- EC2 services active: `stockanalysis-frontend-api.service`, `stockanalysis-web.service`.
- EC2 `/api/data-health` result: `maturity_status=not_due`, `next_due_date=2026-06-20`, `next_due_count=19`, `not_due_count=180`, `ready_for_backfill_count=0`, `due_today_count=0`, `overdue_count=0`, `price_gap_count=0`, `weight_review_status=blocked_by_outcome_calibration_no_due_outcome_window`, `manual_weight_review_allowed=false`.
- EC2 `/data-health` route renders `성과 측정창`, `다음 측정일`, `지연/가격 보강`, and `성과 측정일 대기`.
- local browser tunnel `http://127.0.0.1:13000/data-health` returned HTTP 200.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate outcomes.
- Do not mark weight review ready from quality eval alone.
