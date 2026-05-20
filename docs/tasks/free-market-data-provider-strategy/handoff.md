# Session Handoff

## Active Task

- 이름: free-market-data-provider-strategy
- 담당: Codex
- 날짜: 2026-05-17

## Current Status

- 완료:
  - Alpha Vantage local ledger corrected to `25/day` assumption without provider calls.
  - FastAPI and Next.js local servers restarted.
  - Free provider strategy documented.
  - Twelve Data one-symbol live smoke succeeded for `AAPL`; local Twelve Data ledger now shows `used=1`, `remaining=799`.
  - Twelve Data small priority watchlist smoke succeeded for `MSFT`, `NVDA`, `GOOGL`, and `AMZN`; local Twelve Data ledger now shows `used=5`, `remaining=795`.
  - freshness-aware skip smoke succeeded for the first five Twelve Data symbols with `provider_request_count=0`.
- 진행 중:
  - Twelve Data adapter pilot follow-up is in progress under `market-data-provider-adapter-pilot`.
- 막힌 점:
  - Broad universe price collection still needs a real Twelve Data free key smoke before it can replace Alpha Vantage for daily operations.

## Current Runtime State

- FastAPI: `http://127.0.0.1:8787`
- Next.js: `http://127.0.0.1:3001`
- Local data-health API: HTTP `200`
- Local data-health frontend: HTTP `200`
- Alpha Vantage local ledger for `2026-05-17`: `used=1`, `remaining=24`, `daily_budget=25`

## Decision

- Alpha Vantage is not one call per day. The official free-tier baseline is 25 requests/day.
- 25 requests/day is still not enough for broad universe collection.
- Keep Alpha Vantage as a throttled fallback for small priority watchlists.
- First free broad-market pilot should be Twelve Data because its Basic/Free plan documents 800 API credits/day.
- Second candidate is Polygon Stocks Basic because it documents free 5 API calls/minute and 2 years historical EOD data.
- Third candidate is Financial Modeling Prep because it documents 250 calls/day, but its free historical depth and plan restrictions need endpoint-level validation.
- Stooq can be evaluated as a bulk historical CSV fallback, but it is not a clean official API-first provider.
- Yahoo/yfinance should not be a primary provider because Yahoo does not provide a stable official free finance API for this use case.

## Sources Checked

- Alpha Vantage support and premium pages: 25 requests/day free-tier baseline.
- Twelve Data pricing/support: Basic/Free plan with 800 API credits/day.
- Polygon pricing: Stocks Basic free plan with 5 API calls/minute and 2 years historical EOD data.
- Financial Modeling Prep pricing/FAQ: Basic free plan with 250 calls/day.
- Nasdaq Data Link docs: free and premium datasets exist, but professional applications are recommended to use premium data.
- Yahoo terms and public API status: not suitable as primary official provider for automated market data ingestion.

## Exact Next Step

- exact next step: use `--skip-if-fresh` on every future Twelve Data watchlist run, then expand the watchlist in capped batches while keeping Alpha Vantage as fallback.
