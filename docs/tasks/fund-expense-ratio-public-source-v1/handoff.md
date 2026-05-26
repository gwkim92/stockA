# fund-expense-ratio-public-source-v1 Handoff

## Status

- in progress: this is the immediate next task after `fund-expense-tracking-source-v1`.

## Context

- `fund-expense-tracking-source-v1` completed on commit `450d5e9`.
- SPY fund analysis has SSGA holdings source and `market.daily_price_bar` liquidity evidence.
- Expense ratio remains `not_collected` because the currently stored SSGA holdings artifact contains holdings only.

## Exact Next Step

- exact next step: inspect free/public issuer or ETF metadata sources for auditable expense-ratio value, source date, and redistribution constraints before adding any import or DTO field behavior.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not hard-code expense ratio constants.
- Do not implement tracking error/NAV in this slice.
