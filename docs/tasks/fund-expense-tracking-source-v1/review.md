# fund-expense-tracking-source-v1 Review

## Review Summary

- Completed. The task now distinguishes source-backed liquidity evidence from honest unknown expense/tracking fields for ETF/fund-like instruments.
- SPY fund analysis continues to use SSGA holdings for holdings/portfolio role, uses `market.daily_price_bar` for liquidity, and keeps expense ratio plus tracking error/NAV drift as explicit `not_collected` states.
- No recommendation weights, benchmark splits, score formulas, broker boundaries, or order flows were changed.

## Issues Found

- No blocking issues found in local or EC2 smoke.
- The current SSGA holdings artifact does not contain expense ratio, NAV, premium/discount, or tracking error fields. Keeping those fields unknown is intentional and preferable to guessing.

## Residual Risks

- Expense ratio still needs a separate free public source import.
- NAV/premium-discount and true tracking error still need an auditable source. Current market price bars only support liquidity, not tracking-error or NAV drift.
- SPY liquidity is only as fresh as `market.daily_price_bar`; latest EC2 evidence is `2026-05-20`.

## Verification Evidence

- Local: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter` passed, 61 tests.
- Local: `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- Local: `cd apps/web && npm run typecheck` passed.
- Local: `cd apps/web && npm run build` passed.
- Local: `git diff --check` passed.
- EC2: deployed commit `450d5e9`.
- EC2: `/opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter` passed, 61 tests.
- EC2: `cd apps/web && npm run typecheck` passed.
- EC2: `cd apps/web && npm run build` passed.
- EC2 API smoke: SPY stock and recommendation detail both report `liquidity.status=collected`, `source_name=market.daily_price_bar`, `observation_count=100`, `average_daily_volume=75546352.24`, `average_daily_dollar_volume=51757628999.20085`, `expense_ratio.status=not_collected`, `tracking_error.status=not_collected`, and `order_boundary=read_only_no_order`.
- EC2 route smoke: `/stocks/SPY` and `/recommendations/recommendation-157` render fund liquidity text.
