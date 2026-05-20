# Market Price Daily Ledger Rollover Plan

## Steps

1. Capture current live `/api/data-health` provider budget state.
2. Verify repo-outside data operations runtime env readiness.
3. Run `stockanalysis-operations market-price-daily-run` with `budget-date=2026-05-19` and `freshness-date=2026-05-18`.
4. Inspect artifact stdout/metadata and DB latest price dates.
5. Re-query `/api/data-health` and verify `/data-health` in the browser.
6. Update handoff/review and run AWH/diff verification.

## Non-Goals

- Host scheduler activation
- New scheduler approval record
- New provider account setup
- Scoring, portfolio, benchmark, or trading changes
