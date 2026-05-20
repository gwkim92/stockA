# Market Price Daily Ledger Rollover Review

## Verification

- Before live API state:
  - authorized `GET /api/data-health` returned `overall_status=healthy`.
  - provider budget was `day_missing` for budget date `2026-05-19`.
  - `market.daily_price_bar` latest observation date was `2026-05-15`.
- Runtime readiness:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.operations.cli env-readiness --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env` passed with secret values redacted.
- Market-price daily run:
  - artifact: `/private/tmp/stockanalysis-runtime/artifacts/20260519T010224Z_market-price-daily`.
  - command: `stockanalysis-operations run --job-id market-price-daily -- ... market-price-daily-run --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env --budget-date 2026-05-19 --freshness-date 2026-05-18`.
  - result: 20 requested, 20 provider requests, 20 succeeded, 0 skipped, 0 failed, 2000 bars, budget `800 -> 780`.
  - latest trade date loaded: `2026-05-18`.
- DB verification:
  - expanded watchlist symbols `META`, `TSLA`, `JPM`, `UNH`, `XOM`, `AVGO`, `LLY`, `COST`, `WMT`, `HD`, `PG`, `KO`, `PEP`, `CRM`, `ORCL`, `AMD`, `INTC`, `NFLX`, `DIS`, and `BAC` all show latest `market.daily_price_bar.trade_date=2026-05-18`.
  - each sampled symbol has 101 bars after the run.
- After live API state:
  - authorized `GET /api/data-health` returned `overall_status=healthy`.
  - provider budget is `configured`, budget date `2026-05-19`, used `20`, remaining `780`.
  - `market_price_upsert` latest run is `pipeline-run-89`.
  - `market.daily_price_bar` latest observation date is `2026-05-18`.
- Frontend verification:
  - `/data-health` browser smoke shows `호출 예산 780 / 800`, `pipeline-run-89`, and `market.daily price bar observed · 2026-05-18`.
  - The budget ratio wrap issue was fixed with a `rail-ratio-value` class.
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
- Scheduler boundary:
  - no `launchctl` command was executed.
  - no host LaunchAgents file was written.
  - activation remains `pending_manual_approval`.

## Residual Risks

- This task used 20 real Twelve Data free-tier calls. The repo-local ledger now tracks the use, but account-side usage outside this repo could still differ.
- Freshness target was manually set to `2026-05-18` in this task. The follow-up `market-price-latest-completed-day-policy` task now supplies automatic latest completed market date resolution; external holiday calendar integration is still not included.
- The local DB remains an MVP mix of real market/macro/SEC inputs and bootstrap signal/recommendation fixtures.
