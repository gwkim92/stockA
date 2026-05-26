# fund-nav-premium-discount-source-v1 Handoff

## Status

- in progress: this is the immediate next task after `fund-expense-ratio-public-source-v1`.

## Context

- `fund-expense-ratio-public-source-v1` completed on commit `b8f6e76`.
- SPY fund analysis now has SSGA holdings, market price liquidity, and official expense ratio evidence.
- NAV, market price/NAV premium-discount, and true tracking error remain explicit unknowns.

## Exact Next Step

- exact next step: inspect the official State Street SPDR product page fields for NAV, market price, and their as-of dates, then decide whether `market.fund_metric_snapshot` can store them without a new schema.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not calculate premium/discount unless NAV and market price are both source-backed with disclosed dates.
- Do not label premium/discount as tracking error.
