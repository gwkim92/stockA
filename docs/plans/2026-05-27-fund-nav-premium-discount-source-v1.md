# fund-nav-premium-discount-source-v1 Plan

## Summary

SPY fund analysis now has holdings, liquidity, and expense ratio evidence. The next gap is source-backed NAV and market-price/NAV premium-discount evidence. This task adds it only if a free/public source exposes the required values and dates.

## Result

- Completed on commit `5073119`.
- Official State Street SPDR product page exposes source-backed NAV, bid/ask midpoint, closing price, premium/discount, and as-of dates.
- `market.fund_metric_snapshot` was extended through migration `0028_fund_nav_premium_discount_metrics.sql`.
- EC2 import `run_id=1582` collected NAV `745.571145`, bid/ask midpoint `745.60`, closing price `745.64`, premium/discount `0.00`, and source date `2026-05-22`.
- API and UI now show `NAV 괴리` for SPY stock and recommendation detail.
- True tracking error remains explicit unknown.

## Implementation Order

1. Inspect the official State Street SPDR product page and current repo-outside artifacts for NAV, market price, and as-of dates.
2. Decide whether existing `market.fund_metric_snapshot` can store these metrics.
3. Extend the provider parser/importer only for source-backed values.
4. Expose NAV and premium/discount on stock and recommendation detail in Korean.
5. Keep true tracking error explicit unknown.

## Guardrails

- No paid provider.
- No guessed NAV, premium/discount, or tracking error.
- No recommendation weight changes.
- No live broker submit.
