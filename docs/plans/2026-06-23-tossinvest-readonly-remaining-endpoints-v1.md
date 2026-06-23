# TossInvest Readonly Remaining Endpoints V1 Plan

## Implementation Steps

1. Add `TossInvestSource` datasets for the remaining read-only endpoints.
2. Extend live Toss readonly payload fetch to call calendars once, and symbol-level warnings/orderbook/trades/price-limits for current holdings only.
3. Fetch OPEN and recent CLOSED orders with bounded limits; fetch order details only for a small bounded subset.
4. Normalize these into secret-free summaries in the readonly sync report.
5. Expose summaries in `/api/data-health` and `/api/trading/readiness` via existing Toss payload builders.
6. Add focused tests and verification script.
7. Run local verification, push, deploy, and EC2 smoke.

## Constraints

- No order writes.
- No scheduler activation.
- No account identifiers or Authorization headers in reports.
- No raw full-depth archival schema in this iteration.

## Done Criteria

- All remaining read-only Toss endpoints have request builders and tests.
- Readonly sync report includes market calendar, warnings, market microdata, and order history summaries.
- Existing order boundary remains disabled.
- EC2 smoke confirms read-only endpoint access without secret leakage.
