# fund-expense-tracking-source-v1 Plan

## Summary

The fund analysis panel now explains SPY through holdings and portfolio role, but expense ratio and tracking error/NAV drift are explicit unknowns. This task determines whether free/public or already collected sources can fill those fields without guessing.

## Implementation Order

1. Inspect existing provider artifacts and market tables for NAV, premium/discount, volume/liquidity, and expense ratio fields.
2. If an auditable free source exists, add a small backend runner or DTO lookup that records source name/date/value.
3. If no source exists, keep fields as `not_collected` and improve the UI copy so users know the next required data source.
4. Verify SPY stock/recommendation pages still show holdings analysis and read-only boundary.

## Guardrails

- No paid provider.
- No recommendation weight changes.
- No live broker submit.
- No guessed expense or tracking values.
