# fund-expense-ratio-public-source-v1 Plan

## Summary

SPY fund analysis now has holdings and liquidity evidence, but expense ratio is still unknown. This task adds expense-ratio evidence only if a free/public source can be named and audited.

## Implementation Order

1. Inspect current repo-outside artifacts and source documents for expense-ratio metadata.
2. Identify a free/public issuer or ETF metadata source and verify source date/value availability.
3. Add backend import or DTO lookup only if the value can be source-backed.
4. Render expense ratio source/date/value in Korean on stock and recommendation detail.
5. Keep `not_collected` if no auditable free source is available.

## Guardrails

- No paid provider.
- No guessed constants.
- No recommendation weight changes.
- No live broker submit.
- No tracking error/NAV implementation in this slice.
