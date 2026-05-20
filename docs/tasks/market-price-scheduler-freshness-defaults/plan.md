# Market Price Scheduler Freshness Defaults Plan

## Steps

1. Add market-price scheduler env constants and provider/watchlist/ledger readiness validation.
2. Add `stockanalysis-operations market-price-daily-run` that reads watchlist, ledger, provider, and budget defaults from env.
3. Export scheduler run date from `run_data_operations_scheduler_job.sh` to child commands.
4. Update `market-price-daily` cadence template and activation runbook examples.
5. Add focused unit tests and run local scheduler-boundary smoke with all symbols fresh.
6. Update handoff/review and AWH evidence.

## Non-Goals

- Host scheduler activation
- Broad universe backfill
- Trading calendar/holiday inference
- Scoring or portfolio logic changes
