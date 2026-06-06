# professional-source-gap-actionable-remediation-v1 Handoff

## Status

- completed: local implementation and verification completed; EC2 deployment/execution is blocked by current SSH timeout.
- status: local implementation and verification completed; EC2 deployment/execution is blocked by current SSH timeout.

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

## Not Completed

- EC2 execution and route smoke were not completed in this session because SSH to `34.206.72.213:22` timed out from the current network.
- AAPL `equity_research_artifact` gap was not executed on EC2 for the same reason. Existing command remains:
  - `stockanalysis-operations equity-research-reporting-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-06-06 --symbol AAPL --provider codex_oauth --execute`

## Exact Next Step

- exact next step: when EC2 SSH/network access is available, merge this task to `develop`, pull `develop` on EC2, then run the QQQ Invesco source imports and AAPL equity research artifact command below.

```bash
stockanalysis-operations benchmark-composition-invesco-qqq-import-run --env-file /opt/stockanalysis/runtime/data-operations.env --benchmark-code QQQ --create-missing-instruments --execute
stockanalysis-operations fund-expense-ratio-invesco-qqq-import-run --env-file /opt/stockanalysis/runtime/data-operations.env --symbol QQQ --execute
stockanalysis-operations fund-nav-premium-discount-invesco-qqq-import-run --env-file /opt/stockanalysis/runtime/data-operations.env --symbol QQQ --execute
stockanalysis-operations fund-tracking-difference-invesco-qqq-import-run --env-file /opt/stockanalysis/runtime/data-operations.env --symbol QQQ --execute
stockanalysis-operations equity-research-reporting-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-06-06 --symbol AAPL --provider codex_oauth --execute
```

Then confirm `/api/data-health.open_gates` no longer contains `professional_source_gap_attention`, unless a new non-managed source gap appears.
