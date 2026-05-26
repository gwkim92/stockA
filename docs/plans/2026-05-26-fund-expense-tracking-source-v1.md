# fund-expense-tracking-source-v1 Plan

## Summary

The fund analysis panel now explains SPY through holdings and portfolio role, but expense ratio and tracking error/NAV drift are explicit unknowns. This task determines whether free/public or already collected sources can fill those fields without guessing.

## Result

- Existing SSGA holdings artifacts were checked and only support holdings/coverage evidence.
- Liquidity is now source-backed through already collected `market.daily_price_bar`.
- Expense ratio, NAV drift, and tracking error remain explicit unknown states because no auditable free source is currently stored.
- SPY stock and recommendation detail now show liquidity source, observed date, observation count, average volume, and average dollar volume in Korean.
- Recommendation weights and broker/order flow remain unchanged.

## Implementation Order

1. Inspect existing provider artifacts and market tables for NAV, premium/discount, volume/liquidity, and expense ratio fields.
2. If an auditable free source exists, add a small backend runner or DTO lookup that records source name/date/value.
3. If no source exists, keep fields as `not_collected` and improve the UI copy so users know the next required data source.
4. Verify SPY stock/recommendation pages still show holdings analysis and read-only boundary.

## Verification

- Local and EC2 `tests.test_frontend_live_adapter` passed.
- Local and EC2 Next.js typecheck/build passed.
- EC2 API smoke confirmed SPY liquidity is `collected` from `market.daily_price_bar` with 100 observations.
- EC2 route smoke confirmed `/stocks/SPY` and `/recommendations/recommendation-157` render `유동성`, `평균 거래량`, `평균 거래대금`, and `주문 경계`.

## Guardrails

- No paid provider.
- No recommendation weight changes.
- No live broker submit.
- No guessed expense or tracking values.
