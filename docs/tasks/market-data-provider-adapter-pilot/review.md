# Market Data Provider Adapter Pilot Review

## Verification

- Focused regression passed:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_sources tests.test_market_price tests.test_market_backfill tests.test_market_price_free_backfill tests.test_data_operations_cli tests.test_ingest_cli tests.test_frontend_live_adapter`
- Compile check passed:
  - `/private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src tests`
- Harness passed:
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task market-data-provider-adapter-pilot`
- Diff hygiene passed:
  - `git diff --check`
- Live provider smoke passed:
  - `stockanalysis-operations market-price-free-backfill-run --watchlist /private/tmp/stockanalysis-runtime/watchlists/twelve-data-live-smoke.csv --ledger /private/tmp/stockanalysis-runtime/twelve-data-budget-ledger.json --provider twelve_data --daily-budget 800 --max-requests-per-run 1 --throttle-seconds 1 --outputsize 100 --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - Result: `AAPL`, 100 bars, latest trade date `2026-05-15`, `provider_request_count=1`, `budget_remaining_after=799`, run_id `36`.
- Runtime API/frontend smoke passed:
  - `GET /api/data-health` returned provider `twelve_data`, status `configured`, `used_request_count=1`, `remaining_request_count=799`.
  - `GET /data-health` returned HTTP `200` and rendered the remaining budget count.
- Small priority watchlist smoke passed:
  - `stockanalysis-operations market-price-free-backfill-run --watchlist /private/tmp/stockanalysis-runtime/watchlists/twelve-data-priority-watchlist.csv --ledger /private/tmp/stockanalysis-runtime/twelve-data-budget-ledger.json --provider twelve_data --daily-budget 800 --max-requests-per-run 4 --throttle-seconds 1 --outputsize 100 --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - Result: `MSFT`, `NVDA`, `GOOGL`, and `AMZN` all succeeded with 100 bars each, latest trade date `2026-05-15`, run_id `37` through `40`.
  - Budget ledger moved from `used=1, remaining=799` to `used=5, remaining=795`.
- DB verification passed:
  - `AAPL`, `MSFT`, `NVDA`, `GOOGL`, and `AMZN` all have `market.daily_price_bar` data through `2026-05-15`.
- Updated runtime API/frontend smoke passed:
  - `GET /api/data-health` returned provider `twelve_data`, status `configured`, `used_request_count=5`, `remaining_request_count=795`.
  - `GET /data-health` returned HTTP `200` and rendered `795`/`800`.
- Env readiness passed:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli env-readiness --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`

## Residual Risks

- Live Twelve Data smoke validates connectivity and basic OHLCV persistence, but it is still only one symbol.
- Small priority watchlist smoke now covers five liquid large-cap symbols, but this is still not a broad universe.
- Twelve Data daily `time_series` normalization stores `adjusted_close=close`; actual split/dividend behavior must be compared against known split cases before performance attribution relies on it.
- Provider quota accounting is local ledger based. It prevents this project from over-calling, but it cannot know usage made outside this repo.
- Alpha Vantage remains the default provider for backward compatibility. Operators must set `--provider twelve_data` or `STOCKANALYSIS_MARKET_PRICE_PROVIDER=twelve_data` for the new pilot path.
- Current runner is budget-aware but not freshness-aware. Re-running the same watchlist will spend provider calls again, so duplicate-call avoidance should come before broader expansion.
