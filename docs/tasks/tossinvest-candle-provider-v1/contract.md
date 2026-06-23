# TossInvest Candle Provider V1 Contract

## Task Request

- request: Apply TossInvest market data capabilities to the service beyond portfolio read-only sync, starting with candle/OHLCV data for tracked symbols.
- request: Report whether all TossInvest API capabilities are applied, whether EC2 IP allowlisting is required, and whether TossInvest should replace existing market data providers.

## Goal

- goal: Add a read-only TossInvest candle provider path that can normalize Toss daily candles into the existing `market.daily_price_bar` model while preserving current provider fallbacks and never enabling broker order writes.

## Scope

- Add TossInvest source support for `GET /api/v1/candles`.
- Add TossInvest candle normalization for daily OHLCV bars.
- Allow the existing market price ingest path to select `provider=tossinvest`.
- Add focused tests for request building, secret redaction, normalization, and unsupported interval behavior.
- Add a small verification script for the Toss candle provider task.
- Document the operational decision: TossInvest can become a primary market data candidate only after IP allowlist and rate-limit stability are proven; existing providers remain fallback.

## Non-Goals

- No Toss order submit, modify, cancel, or order-history mutation.
- No scheduler provider switch in production until live Toss access is unblocked and verified.
- No removal of Twelve Data, Alpha Vantage, FRED, SEC, news, fundamentals, or other non-overlapping providers.
- No recommendation scoring weight, benchmark, paper validation, or live broker boundary changes.

## Safety Requirements

- Credentials must come from repo-outside env only.
- Reports, logs, and tests must not expose client secrets, bearer tokens, account numbers, or Authorization headers.
- Toss provider access errors must be reported without secret leakage.
- `broker_submit_allowed=false`, `automatic_order_allowed=false`, and `order_boundary=read_only_no_order` remain enforced.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/ingest/sources/tossinvest.py`
  - `src/stockanalysis/ingest/market/price.py`
  - Toss-focused tests
  - verification scripts
  - task plan, contract, and handoff documents

Do not mutate deployment secrets, scheduler activation, broker submit/order endpoints, recommendation scoring, benchmark definitions, or existing portfolio positions.

## Verification Commands

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_tossinvest_source tests.test_market_price`
- verification command: `bash scripts/verify_tossinvest_candle_provider.sh`
- broader verification if touched paths require it: `PYTHONPATH=src python3 -m unittest`
