# recommendation-outcome-calibration-sample-expansion-v1 Handoff

## Status

- completed: implemented and EC2-smoked recommendation outcome calibration sample expansion.

## Context

- Professional analysis evidence now exists for company financials, valuation, SOTP, thesis lifecycle, portfolio risk, position sizing, and ETF/fund source metrics.
- Recommendation weights remain intentionally unchanged because outcome evidence is still too sparse for a defensible calibration change.
- The next useful move toward the project goal is not another UI label pass. It is outcome/calibration evidence that can prove whether the professional components improve medium-long recommendation quality.

## Exact Next Step

- exact next step: move to `recommendation-weight-review-horizon-gate-v1` so the manual weight review readiness path consumes the new horizon-grid outcome calibration gate instead of trusting the older quality eval alone.

## Implementation Evidence

- local commit: `5de2ef8` (`Add recommendation outcome calibration sample expansion`).
- guardrail fix commit: `8c3cbb1` (`Guard outcome calibration when horizons are not due`).
- new CLI: `stockanalysis-operations recommendation-outcome-calibration-sample-expansion-run`.
- new backend service: `src/stockanalysis/operations/recommendation_outcome_calibration_sample_expansion.py`.
- new UI visibility: `/api/data-health` and `/data-health` expose recommendation outcome calibration status, horizon counts, outcome counts, backfill candidates, price gaps, component diagnostic count, next action, and read-only order boundary.
- EC2 execute: `run_id=1595`, `eval_run_id=27`, nested backfill `run_id=1596`, nested quality eval `eval_run_id=26`.
- EC2 result: `score_status=no_due_outcome_window`, `recommendation_horizon_count=180`, `recommendation_count=45`, `outcome_count=0`, `not_due_count=180`, `ready_for_backfill_count=0`, `component_diagnostic_count=10`.
- Guardrail: `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.

## Verification Evidence

- local: `PYTHONPATH=src python3 -m unittest tests.test_recommendation_outcome_calibration_sample_expansion tests.test_recommendation_outcome_backfill tests.test_recommendation_quality_eval tests.test_data_operations_cli tests.test_frontend_live_adapter` passed, 158 tests.
- local: `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- local: `cd apps/web && npm run typecheck` passed.
- local: `cd apps/web && npm run build` passed.
- EC2: same focused Python suite passed, 158 tests.
- EC2: `cd apps/web && npm run typecheck` passed.
- EC2: `cd apps/web && npm run build` passed.
- EC2 API smoke: `/api/data-health` returned `recommendation_outcome_calibration.status=no_due_outcome_window`, `eval_run_id=eval-run-27`, `outcome_count=0`, `not_due=180`.
- EC2 route smoke: `/data-health` rendered `추천 성과검증`, `성과 측정일 대기`, `추천 weight를 바꾸기 전에`, `성과 표본`, and `주문 경계`.

## Guardrails

- Keep all recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate outcomes for missing price history.
- Do not change benchmark splits without explicit approval.
