# TossInvest Readonly Remaining Endpoints V1 Contract

## Task Request

- request: Attach the remaining read-only TossInvest Open API endpoints that were not included in the first TossInvest foundation tasks.
- request: Keep real broker order submission, modification, and cancellation disabled.

## Goal

- goal: The existing TossInvest readonly sync/report surface includes market calendars, stock warnings, orderbook, recent trades, price limits, and order history/detail summaries without exposing secrets or enabling writes.

## Scope

- Add request builders for:
  - `GET /api/v1/market-calendar/KR`
  - `GET /api/v1/market-calendar/US`
  - `GET /api/v1/stocks/{symbol}/warnings`
  - `GET /api/v1/orderbook`
  - `GET /api/v1/trades`
  - `GET /api/v1/price-limits`
  - `GET /api/v1/orders`
  - `GET /api/v1/orders/{orderId}`
- Extend `stockanalysis-operations tossinvest-readonly-sync-run` output with bounded read-only summaries for the new endpoints.
- Persist those summaries in the existing `ops.pipeline_run.config_json` report metadata path, not in new trading/order mutation tables.
- Expose the new read-only summaries through existing frontend API read models where Toss sync/readiness is already surfaced.
- Add focused tests and a verification script.

## Non-Goals

- No `POST /api/v1/orders`.
- No modify/cancel calls.
- No scheduler activation or default market-data provider switch.
- No recommendation weight, benchmark, portfolio rebalance, or broker order boundary change.
- No long-term archival schema for full tick/trade/orderbook depth in this task.

## Safety Requirements

- Credentials must come from repo-outside env only.
- Do not log Toss client secret, bearer token, account sequence/account number, Authorization header, or raw full account identifiers.
- Order history is read-only evidence only. It must never drive automatic order placement.
- `broker_submit_allowed=false`, `automatic_order_allowed=false`, `order_boundary=read_only_no_order`, `submitted_to_broker=false` remain enforced.
- Keep live calls bounded: only current holdings symbols; recent trades count capped; closed order history capped; order detail capped.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/ingest/sources/tossinvest.py`
  - `src/stockanalysis/operations/tossinvest_readonly_sync.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - Toss-focused tests and verification scripts
  - task plan, contract, and handoff documents

Do not mutate order submit adapters except for tests proving they remain disabled, deployment secrets, recommendation scoring, benchmark definitions, or live scheduler activation.

## Verification Commands

- verification command: `bash scripts/verify_tossinvest_remaining_readonly_endpoints.sh`
- verification command: `bash scripts/verify_tossinvest_readonly_currency_foundation.sh`
- verification command: `PYTHONPATH=src /tmp/stockanalysis-tossinvest-venv/bin/python -m unittest discover -s tests`
