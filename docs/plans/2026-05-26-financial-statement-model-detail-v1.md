# financial-statement-model-detail-v1 Plan

## Summary

Expose the existing normalized financial statement model on stock detail pages so the professional analysis flow shows actual financial evidence, not only zero-weight score components.

## Scope

- Read existing `market.financial_metric_normalized` and raw `shares_outstanding` data.
- Build a stock detail DTO section grouped by analyst categories: growth, profitability, cash flow, balance sheet, capital intensity, earnings quality, and dilution/share count.
- Render the model in Korean on `/stocks/[symbol]`.
- Keep recommendation score weights, benchmark/evaluation splits, and broker/order boundaries unchanged.

## Implementation Notes

- The API should prefer the most recent computed value for each metric, while still exposing latest-period gaps through status counts and data-gap counts.
- The UI should present missing values as data gaps, not silently hide them.
- This is a visibility task. It does not add new financial formulas.

## Verification

- Focused stock detail API unit tests.
- Full live adapter tests.
- Python compileall.
- Next.js typecheck and build.
- Project roadmap verifier.
- AWH task verifier.
- EC2 read-only SQL smoke before deployment and route/API smoke after deployment.
