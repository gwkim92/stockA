# fund-nav-premium-discount-source-v1 Review

## Review Summary

- Pass. The task adds source-backed NAV and market-price/NAV premium-discount evidence without guessing tracking error, changing recommendation weights, or enabling broker/order flow.

## Issues Found

- None blocking.
- One deployment issue was found and resolved: initial route smoke did not show `NAV 괴리` because EC2 Next.js production build had not been regenerated after deploy. Running `npm run build` and restarting `stockanalysis-web.service` fixed it.

## Residual Risks

- The value is a one-day NAV/market-price premium-discount observation, not a multi-period tracking error.
- The parser depends on the current State Street SPDR product page shape. If the provider HTML changes, the import should fail rather than silently guess.
- Only SPY is smoke-tested in this slice. Broader ETF coverage should be added through separate source-backed provider tasks.

## Verification Evidence

- Local focused tests:
  - `PYTHONPATH=src python3 -m unittest tests.test_fund_expense_ratio_provider`: 7 tests OK.
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`: 61 tests OK.
  - `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli`: 78 tests OK.
- Local full Python tests with Python 3.13 verify venv:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`: 1003 tests OK.
- Local frontend:
  - `cd apps/web && npm run typecheck`: passed.
  - `cd apps/web && npm run build`: passed.
- Local official-source dry-run:
  - `fund-nav-premium-discount-ssga-spdr-import-run --dry-run` parsed NAV `745.571145`, bid/ask midpoint `745.60`, closing price `745.64`, premium/discount `0.00`, source date `2026-05-22`.
- EC2 migration:
  - `db/migrations/0028_fund_nav_premium_discount_metrics.sql` applied through stdin to `STOCKANALYSIS_PSQL_COMMAND`.
- EC2 focused tests:
  - `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_fund_expense_ratio_provider tests.test_frontend_live_adapter tests.test_data_operations_cli`: 146 tests OK.
  - `cd apps/web && npm run typecheck`: passed.
  - `cd apps/web && npm run build`: passed.
- EC2 import:
  - `run_id=1582`, `fund_metric_snapshot_ids=[2,3,4,5]`, `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- EC2 API smoke:
  - `/api/stocks/SPY`: `nav_premium_discount.status=collected`, NAV `745.571145`, closing price `745.64`, premium `0.0`, source date `2026-05-22`, expense ratio remains `0.000945`, order boundary read-only.
  - `/api/recommendations/recommendation-157`: same NAV/premium-discount evidence and read-only boundary.
- EC2 route smoke:
  - `/stocks/SPY` and `/recommendations/recommendation-157`: all expected text present: `NAV 괴리`, `NAV 원천 열기`, `US$745.57`, `0%`, `비용률`, `주문 경계`.
