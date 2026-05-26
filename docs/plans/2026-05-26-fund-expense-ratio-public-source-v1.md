# fund-expense-ratio-public-source-v1 Plan

## Summary

SPY fund analysis now has holdings and liquidity evidence, but expense ratio is still unknown. This task adds expense-ratio evidence only if a free/public source can be named and audited.

## Result

- Free official source selected: State Street SPDR SPY product page.
- Stored table: `market.fund_metric_snapshot`.
- Runner: `stockanalysis-operations fund-expense-ratio-ssga-spdr-import-run`.
- EC2 source-backed result: Gross Expense Ratio `0.094500%`, stored as ratio `0.000945`, source date `2026-05-26`, run `1581`.
- Stock and recommendation detail now render the source-backed value in Korean with source/date/link.
- NAV, premium/discount, and tracking error remain out of scope.

## Implementation Order

1. Inspect current repo-outside artifacts and source documents for expense-ratio metadata.
2. Identify a free/public issuer or ETF metadata source and verify source date/value availability.
3. Add backend import or DTO lookup only if the value can be source-backed.
4. Render expense ratio source/date/value in Korean on stock and recommendation detail.
5. Keep `not_collected` if no auditable free source is available.

## Verification

- Local and EC2 focused Python tests passed.
- Local and EC2 Next.js typecheck/build passed.
- EC2 migration and import smoke passed.
- EC2 API and route smoke confirmed SPY expense ratio visibility.

## Guardrails

- No paid provider.
- No guessed constants.
- No recommendation weight changes.
- No live broker submit.
- No tracking error/NAV implementation in this slice.
