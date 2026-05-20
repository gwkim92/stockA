# Review Notes

- Implemented local provider budget protection in Python backend operations code, not shell orchestration.
- Added `stockanalysis-operations market-price-free-backfill-run`.
- The runner reads a repo-outside CSV watchlist and repo-outside JSON ledger, calculates remaining daily provider budget, and delegates to the existing market price batch upsert with `max_requests_per_run` capped to the remaining budget.
- The ledger records per-provider/per-day used request counts and per-run summaries.
- The no-quota smoke proved the runner can execute and update the ledger without consuming Alpha Vantage calls.

## Remaining Risks

- The ledger is local host state. It does not protect a second machine or a manually triggered provider call outside this runner.
- Provider-side daily quota can still be exhausted before local ledger knows about it.
- The ledger is not yet surfaced in FastAPI/Next.js, so visibility is currently CLI/file based.
- Free `TIME_SERIES_DAILY` prices remain unadjusted.
