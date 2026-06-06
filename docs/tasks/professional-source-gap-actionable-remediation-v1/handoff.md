# professional-source-gap-actionable-remediation-v1 Handoff

## Status

- completed: implemented, pushed to `develop`, deployed to EC2, executed on EC2, and route/API-smoked.
- status: completed.

## Completed

- Added official Invesco QQQ benchmark composition import:
  - `stockanalysis-operations benchmark-composition-invesco-qqq-import-run`
  - Source: `https://dng-api.invesco.com/cache/v1/accounts/en_US/shareclasses/QQQ/holdings/fund?idType=ticker&interval=monthly&productType=ETF`
  - Normalizes QQQ common stock, ADR, and depositary receipt holdings.
  - Skips futures, cash, cash collateral, and synthetic cash rows.

- Added official Invesco QQQ fund metric imports:
  - `stockanalysis-operations fund-expense-ratio-invesco-qqq-import-run`
  - `stockanalysis-operations fund-nav-premium-discount-invesco-qqq-import-run`
  - `stockanalysis-operations fund-tracking-difference-invesco-qqq-import-run`
  - Expense ratio stores `net_expense_ratio`.
  - NAV stores `nav_per_share`.
  - Performance stores `tracking_difference_nav_1_year`, `3_year`, `5_year`, `10_year` against NASDAQ-100 Index. This is tracking difference, not tracking error.

- Updated `/api/data-health` professional source gap remediation routing:
  - SPY fund source gaps route to SSGA SPDR runners.
  - QQQ fund source gaps route to Invesco QQQ runners.
  - Unknown ETF providers no longer receive SPY-specific SSGA commands.
  - Existing broker/order boundary remains `read_only_no_order`.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_benchmark_composition_provider tests.test_fund_expense_ratio_provider tests.test_data_operations_cli tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
- Passed: `git diff --check`
- Dry-run: `benchmark-composition-invesco-qqq-import-run --dry-run`
  - `component_count=101`
  - `target_weight_total=0.99938504`
  - `coverage_status=full_enough_for_drift`
  - `automatic_order_allowed=false`
  - `broker_submit_allowed=false`
- Dry-run: Invesco QQQ expense/NAV/tracking runners
  - expense: `net_expense_ratio=0.0018`
  - NAV: `nav_per_share=705.040931`
  - tracking metric count: `4`
- EC2 deployment:
  - pulled `develop` to commit `aed06a61`
  - restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`
  - both services returned `active`
- EC2 QQQ execution:
  - `benchmark_composition_invesco_qqq_import`: `status=completed`, `component_count=101`, `coverage_status=full_enough_for_drift`, source date `2026-06-06`
  - `fund_expense_ratio_invesco_qqq_import`: `status=completed`, `run_id=3750`
  - `fund_nav_premium_discount_invesco_qqq_import`: `status=completed`, `run_id=3751`, `metric_count=1`
  - `fund_tracking_difference_invesco_qqq_import`: `status=completed`, `run_id=3752`, `metric_count=4`
- EC2 AAPL execution:
  - `equity_research_reporting`: `status=completed`, `run_id=3753`, `provider=codex_oauth`, `model_name=codex-cli-default`, `failed_artifact_count=0`
- EC2 `/api/data-health`:
  - `overall_status=healthy`
  - `open_gates=[]`
  - `professional_source_gap_prioritization.attention_required=false`
  - `fund_source_gap_count=0`
  - `coverage_gap_count=0`
  - `professional_analysis_quality.status=managed_source_limited`
  - active candidates `26`, complete candidates `25`, source blocked `1`, average coverage `0.9712`
  - `automatic_weight_change_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`
- EC2 route smoke:
  - `/` `200`
  - `/data-health` `200`
  - `/stocks/QQQ` `200`
  - `/stocks/AAPL` `200`

## Not Completed

- Nothing remains for this task. EROK remains visible as a managed source blocker and is blocked from professional decision/paper validation input until standard periodic filings or a dedicated parser exist.

## Exact Next Step

- exact next step: continue with the next open product-quality task after `professional_source_gap_attention`; do not start manual weight review until the outcome maturity due date and router allow it.
