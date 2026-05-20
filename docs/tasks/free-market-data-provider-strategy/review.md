# Free Market Data Provider Strategy Review

## Verification

- PASS: FastAPI restarted and `/__health` returned HTTP `200`.
- PASS: protected `/api/data-health` returned HTTP `200`.
- PASS: Next.js restarted and `/`, `/data-health` returned HTTP `200`.
- PASS: `/data-health` rendered Korean labels and Alpha Vantage local provider budget `24/25`.
- PASS: Alpha Vantage ledger correction consumed `0` provider calls.

## Residual Risks

- Local Alpha Vantage ledger is not the provider's authoritative account-side counter.
- Free plans can change, throttle, or restrict endpoints without notice.
- Free market data license terms may not permit redistribution or public display. This project should treat free providers as local/private research inputs unless a provider explicitly allows broader use.
- Adjusted prices remain unresolved for free Alpha Vantage; provider pilot must verify split/dividend adjustment semantics.
