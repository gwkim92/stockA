# fund-nav-premium-discount-source-v1 Plan

## Summary

SPY fund analysis now has holdings, liquidity, and expense ratio evidence. The next gap is source-backed NAV and market-price/NAV premium-discount evidence. This task adds it only if a free/public source exposes the required values and dates.

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
