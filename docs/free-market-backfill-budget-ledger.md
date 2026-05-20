# Free Market Backfill Budget Ledger

This task adds local cross-run quota protection for free Alpha Vantage market-price backfills.

The design keeps watchlist and ledger files outside the repository. The operations runner reads those files, computes the remaining daily provider request budget, and delegates actual price ingestion to the existing Python batch upsert.

## Implemented Behavior

- Command: `stockanalysis-operations market-price-free-backfill-run`.
- Inputs:
  - `--watchlist`: repo-outside CSV with a required `symbol` column.
  - `--ledger`: repo-outside JSON file that persists provider/day request usage.
  - `--daily-budget`: default `25`.
  - `--max-requests-per-run`: default `25`.
  - `--throttle-seconds`: default `1`.
- Path policy rejects repo-inside watchlist and ledger paths.
- The runner caps the batch upsert request budget to `min(max_requests_per_run, daily_budget - used_request_count)`.
- If no request budget remains, it does not call the provider-backed batch upsert.
- Ledger writes are atomic via same-directory temp file replacement.

## Local Smoke

- Watchlist: `/private/tmp/stockanalysis-runtime/watchlists/free-market-watchlist.csv`.
- Ledger: `/private/tmp/stockanalysis-runtime/alpha-vantage-budget-ledger.json`.
- Smoke command used `--max-requests-per-run 0`, so it consumed zero Alpha Vantage calls.
- Smoke result: `status=no_provider_request_budget`, `provider_request_count=0`, `requested_symbol_count=3`.

## Next Boundary

The next useful slice is visibility: expose this ledger/backfill status through FastAPI `/api/data-health` or a dedicated operations panel so the frontend shows remaining daily provider budget before any broad backfill is attempted.
