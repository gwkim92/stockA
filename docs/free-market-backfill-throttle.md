# Free Market Backfill Throttle

This task adds no-cost market data guardrails for Alpha Vantage free-tier operation.

The job must space provider requests and cap total requests per run so the project can continue without paid data subscriptions.

## Implemented Behavior

- `stockanalysis-ingest market-price-batch-upsert` accepts `--throttle-seconds` and `--max-requests-per-run`.
- `stockanalysis-ingest market-price-universe-backfill` forwards the same controls after selecting canonical symbols.
- Provider-backed requests are counted only when no local fixture is used.
- Symbols beyond the configured request budget are returned as `status=skipped` with `reason=request_budget_exhausted`; they do not call Alpha Vantage and do not fail the run.
- The daily market cadence reference command now includes `--throttle-seconds 1 --max-requests-per-run 25`.

## Verification Snapshot

- Unit/CLI/cadence tests passed on 2026-05-17 with the Python 3.13 runtime venv.
- Real free-provider smoke used `max_requests_per_run=1`; AAPL loaded 100 daily bars through run_id `34`, while MSFT was intentionally skipped by the request budget.
- FastAPI `/api/data-health` returned HTTP `200` after the run and reflected latest `market_price_upsert` status as succeeded.

## Next Boundary

This slice is per-run protection. A future orchestration slice should persist a watchlist queue and daily provider budget ledger before any broad universe backfill is attempted.
