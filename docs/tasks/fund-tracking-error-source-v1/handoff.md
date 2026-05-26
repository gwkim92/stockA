# fund-tracking-error-source-v1 Handoff

## Status

- completed: implemented source-backed SPY tracking difference import and EC2-smoked it.

## Context

- SPY fund analysis currently has source-backed holdings, liquidity, expense ratio, NAV, market price, and premium/discount evidence.
- True multi-period tracking error remains explicitly unknown because the official State Street SPDR product page does not publish a numeric tracking error field.
- The official State Street SPDR product page does publish month-end NAV total return before tax and benchmark return windows. The task stores the difference as `tracking_difference`, not as `tracking_error`.
- One-day NAV premium/discount remains separate from tracking difference.

## Implementation Evidence

- local commit: `05cdd2a` (`Add source-backed fund tracking difference import`).
- migration: `db/migrations/0029_fund_tracking_difference_metrics.sql`.
- CLI: `stockanalysis-operations fund-tracking-difference-ssga-spdr-import-run`.
- EC2 import: `run_id=1592`, `fund_metric_snapshot_ids=[6,7,8,9,10,11,12,13]`, `metric_count=8`.
- source: `ssga_spdr_product_page`.
- stored representative metric: `tracking_difference_nav_1_year=-0.0021`, `fund_return=0.3084`, `benchmark_return=0.3105`, `benchmark_name=S&P 500 Index`, `source_as_of_date=2026-04-30`, `measurement_basis=nav_total_return_before_tax`.
- `/api/stocks/SPY` and `/api/recommendations/recommendation-157` expose `tracking_error.status=tracking_difference_collected`, `metric_type=tracking_difference`, `value=null`, `tracking_difference_value=-0.0021`, and `order_boundary=read_only_no_order`.
- `/stocks/SPY` and `/recommendations/recommendation-157` render `추적오차/추적차이`, `추적차이 원천 열기`, `기간 1 Year`, `S&P 500 Index`, `NAV 수익률 30.8%`, and `벤치마크 31.1%`.

## Verification Evidence

- local: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli tests.test_frontend_live_adapter tests.test_fund_expense_ratio_provider` passed, 149 tests.
- local: `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- local: `cd apps/web && npm run typecheck` passed.
- local: `git diff --check` passed.
- EC2: same focused Python suite passed, 149 tests.
- EC2: `cd apps/web && npm run typecheck` passed.
- EC2: `cd apps/web && npm run build` passed.
- EC2: FastAPI health and Next route probes returned HTTP 200.

## Exact Next Step

- exact next step: move to `recommendation-outcome-calibration-sample-expansion-v1`, because professional analysis components now exist but recommendation weight changes remain blocked until outcome/calibration evidence is stronger.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not label tracking difference as tracking error.
- Do not infer tracking error from one-day NAV premium/discount.
- Do not introduce paid providers.
