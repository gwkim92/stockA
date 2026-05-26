# fund-expense-ratio-public-source-v1 Review

## Review Summary

- Completed. SPY ETF expense ratio is now imported from the official State Street SPDR product page and persisted as source-backed fund metric evidence.
- The value is not hard-coded in the frontend or DTO. It is parsed by a backend operation, stored in `market.fund_metric_snapshot`, and read by stock/recommendation live adapters.
- Recommendation weights and broker/order flow were not changed.

## Issues Found

- No blocking issues found in local or EC2 smoke.
- The official page exposes Gross Expense Ratio and fund information date, but this task intentionally does not treat that as tracking error or NAV evidence.

## Residual Risks

- Expense ratio freshness depends on re-running `fund-expense-ratio-ssga-spdr-import-run`.
- The current system has a manual/CLI import path; it is not yet added to a recurring profile scheduler.
- NAV, premium/discount, and true tracking error are still not collected.

## Verification Evidence

- Local unit/CLI/frontend adapter focused tests passed: `tests.test_fund_expense_ratio_provider`, `tests.test_frontend_live_adapter`, `tests.test_data_operations_cli`.
- Local `compileall`, Next.js typecheck/build, and diff check passed.
- EC2 migration `0027_fund_metric_snapshot` applied.
- EC2 import completed: `run_id=1581`, `fund_metric_snapshot_id=1`, Gross Expense Ratio `0.094500%`, source date `2026-05-26`.
- EC2 API smoke confirmed SPY stock and recommendation details return `expense_ratio.status=collected`, `value=0.000945`, source `ssga_spdr_product_page`, and `order_boundary=read_only_no_order`.
- Route smoke confirmed SPY stock and recommendation pages render `0.0945%` and the source link text.
