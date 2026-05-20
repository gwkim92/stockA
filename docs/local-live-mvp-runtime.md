# Local Live MVP Runtime

This task prepares the first local live MVP path: real/local Postgres, FastAPI read-only backend, Next.js cockpit, and one-shot data operations smoke before any recurring scheduler activation.

It does not execute `launchctl`, does not write LaunchAgents, and does not create production secrets.

Runtime files are kept outside the repository under `/private/tmp/stockanalysis-runtime`.

## Current Local Runtime

- Postgres: Docker container `stockanalysis-local-postgres`, exposed on `127.0.0.1:55432`.
- FastAPI read-only backend: `http://127.0.0.1:8787`.
- Next.js cockpit: `http://127.0.0.1:3001`.
- 3000 is currently occupied by an unrelated `llm-wiki` Next server and was not terminated.

## Verified Scope

- Repo migrations and seeds were applied to the local Postgres runtime.
- One-shot `macro-weekly` data operations smoke wrote artifacts outside the repository.
- Fixture-backed market, SEC, event, theme, cycle, recommendation, thesis, performance, portfolio, attribution, and remediation data were loaded into the local DB.
- Real-provider FRED macro data and SEC filing metadata were loaded after runtime bootstrap.
- Real-provider AAPL prices were loaded through the no-cost Alpha Vantage `TIME_SERIES_DAILY` endpoint; these rows use `price_adjustment_mode=unadjusted_fallback`.
- Free-tier market batch backfill now supports per-run request caps and call spacing; a capped smoke loaded AAPL and skipped MSFT without a second provider call.
- Free-tier market backfill now has a repo-outside watchlist and JSON daily provider budget ledger runner under `stockanalysis-operations`; the no-quota smoke consumed zero Alpha Vantage calls.
- `/api/data-health` and the Next `/data-health` page now show sanitized free-tier provider budget status from the local ledger.
- Codex OAuth was verified as a no-API-key local LLM provider for offline SEC event extraction jobs.
- FastAPI live probes and authorized read-only routes were verified against the local DB.
- Next.js cockpit routes `/`, `/data-health`, `/cycles`, `/events`, and `/recommendations/AAPL-2024-11-01` returned HTTP 200 against the live backend.

## Out Of Scope

- Real-provider API ingestion credentials.
- Split/dividend-adjusted market prices from premium endpoints.
- Recurring host scheduler activation.
- Paper trading and real trading flows.
- Production deployment manifests and observability stack activation.
