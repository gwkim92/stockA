# fund-tracking-error-source-v1 Handoff

## Status

- pending: this is the immediate next task after `fund-nav-premium-discount-source-v1`.

## Context

- SPY fund analysis currently has source-backed holdings, liquidity, expense ratio, NAV, market price, and premium/discount evidence.
- True multi-period tracking error remains explicitly unknown.
- The previous NAV premium/discount task intentionally avoided labeling one-day NAV gap as tracking error.

## Exact Next Step

- exact next step: inspect official State Street SPDR data and other free/public ETF sources for published tracking error, tracking difference, or fund-vs-benchmark return windows with source dates.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not infer tracking error from one-day NAV premium/discount.
- Do not introduce paid providers.
