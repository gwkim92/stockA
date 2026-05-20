# Session Handoff

## Active Task

- 이름: local-market-universe-live-bootstrap
- 담당: Codex
- 날짜: 2026-05-17

## Current Status

- 완료:
  - SEC `company_tickers_exchange` request builder no longer requires `cik`.
  - `market-universe-weekly` cadence registration added.
  - market price instrument lookup now preserves non-empty psql execution errors instead of reporting every psql failure as missing instrument.
  - live SEC universe bootstrap succeeded against local Postgres.
  - `MSFT`, `NVDA`, and `AAPL` now resolve through the same instrument lookup path used by price upsert.
- 진행 중:
  - none.
- 막힌 점:
  - Alpha Vantage free-tier scale remains insufficient for broad universe operations. The local ledger now shows 24 remaining calls for 2026-05-17, but this is local accounting only.

## Background

- 2026-05-17 positive-budget market price run consumed one free Alpha Vantage call.
- The provider call failed at DB upsert because `MSFT` had no canonical instrument row.
- `NVDA` and `AAPL` were skipped after the one-call daily budget was exhausted.
- The correct fix is to bootstrap canonical instruments from SEC listed company ticker/exchange data, not to insert manual ticker rows.

## Implemented

- `src/stockanalysis/ingest/sources/sec.py`: CIK normalization moved into CIK-bound SEC dataset branches.
- `tests/test_ingest_sources.py`: added regression coverage for CIK-free `company_tickers_exchange` request creation.
- `src/stockanalysis/operations/cadence.py`: added `market-universe-weekly` data operation job for `market_universe_bootstrap`.
- `tests/test_data_operations_cadence.py`: added cadence report and expected SQL coverage for the universe job.
- `src/stockanalysis/ingest/market/price.py`: only maps the explicit scalar no-row sentinel to missing canonical instrument.
- `tests/test_market_price.py`: added regression coverage for psql lookup errors.

## Verification

- PASS: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_sources tests.test_market_universe tests.test_data_operations_cadence tests.test_data_operations_artifact_runner tests.test_market_price`
- PASS: `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python scripts/smoke_data_operations_runtime.sh --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env --job-id market-universe-weekly --timeout-seconds 240 -- /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.ingest.cli market-universe-bootstrap --exchange Nasdaq --exchange NYSE`
- PASS: live SEC universe summary selected 7,562 records across Nasdaq/NYSE with run_id `35`.
- PASS: local Postgres query returned active `AAPL|XNAS`, `MSFT|XNAS`, and `NVDA|XNAS` listed securities.
- PASS: price upsert instrument resolver returned canonical rows for `MSFT`, `NVDA`, and `AAPL`.
- PASS: `git diff --check`

## Exact Next Step

- exact next step: document and pilot a free market data provider strategy. Keep Alpha Vantage as a throttled fallback for small priority watchlists.
