# fund-tracking-error-source-v1 Review

## Review Summary

- No blocking findings found in the implemented scope.
- The implementation correctly distinguishes source-backed `tracking_difference` from true `tracking_error`.
- The one-year SPY value comes from official State Street SPDR month-end NAV return minus benchmark return, not from one-day NAV premium/discount.

## Issues Found

- None found in review.

## Residual Risks

- True tracking error remains unavailable from the inspected free official source, so `tracking_error.value` intentionally remains `null`.
- The current implementation covers SPY/State Street SPDR product-page parsing first. Broader fund families or ETF symbols need a separate source-breadth task.
- Source HTML layout changes at State Street can break parsing; the parser has unit fixtures but still depends on the public page structure.

## Verification Evidence

- local: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli tests.test_frontend_live_adapter tests.test_fund_expense_ratio_provider` passed, 149 tests.
- local: `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- local: `cd apps/web && npm run typecheck` passed.
- local: `git diff --check` passed.
- EC2: focused Python suite passed, 149 tests.
- EC2: `cd apps/web && npm run typecheck` passed.
- EC2: `cd apps/web && npm run build` passed.
- EC2 import: `run_id=1592`, `metric_count=8`, `tracking_difference_nav_1_year=-0.0021`.
- EC2 API smoke: `/api/stocks/SPY` and `/api/recommendations/recommendation-157` returned `tracking_difference_collected`, `metric_type=tracking_difference`, `value=null`, `order_boundary=read_only_no_order`.
- EC2 route smoke: `/stocks/SPY` and `/recommendations/recommendation-157` rendered the tracking difference source, period, benchmark, fund return, and benchmark return.
