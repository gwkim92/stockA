# Task Contract

## Task Request

- name: `cross-asset-provider-quality-and-market-map-v1`
- request: Resolve the remaining cross-asset quality gaps after `cross-asset-etf-watchlist-price-refresh-v1`.

## Objective

Add an explicit `XAG_USD` Twelve Data symbol fallback policy, make stale FRED dollar index handling explicit without imputing values, and add a user-facing `/market-map` page/API DTO for index, rates, dollar, commodity, volatility, credit, and crypto/liquidity flows.

## Goal

- goal: cross-asset ingestion records bounded Twelve Data symbol fallback evidence for silver, stale FRED dollar index observations remain visibly stale with weakened confidence instead of synthetic fills, and the cockpit exposes a read-only `/market-map` route that explains current index/rates/dollar/commodity/volatility flows in user language.

## Scope

- Add `XAG_USD` symbol fallback attempts for Twelve Data provider reads.
- Add stale policy evidence for `USD_BROAD_INDEX`.
- Add read-only live/fixture frontend contract for `/api/market-map`.
- Add Next.js `/market-map` page and home navigation link.
- Add regression tests for provider fallback, stale policy evidence, live adapter DTO, fixture contract, and read-only SQL boundaries.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/cross_asset_market.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/frontend/api_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/market-map/page.tsx`
  - `docs/api/frontend/contract-index.json`
  - `docs/api/frontend/examples/market-map.json`
  - `tests/test_cross_asset_market.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_fixture_server.py`
  - `docs/tasks/cross-asset-provider-quality-and-market-map-v1/*`

## Out Of Scope

- Recommendation score weight changes.
- Benchmark definition changes.
- Portfolio position changes.
- Broker/order/write API changes.
- Paid data providers.
- Raw provider feed redistribution.

## Decisions

- `XAG_USD` keeps Twelve Data as the free provider but tries a bounded symbol fallback list. It starts with `XAG/USD` and can fall back to `XAGUSD` and `SILVER`.
- Fallback attempts are recorded in redacted observation evidence. Failed attempts are surfaced in the runner report without exposing API keys.
- FRED `USD_BROAD_INDEX` stale data is not imputed. It remains `freshness_status=stale`, receives low confidence, and the frontend explains that dollar-pressure conclusions are weakened until FRED refreshes.
- `/market-map` is read-only and shows deterministic evidence only. It must not make causal claims or imply live trading readiness.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cross_asset_market tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_frontend_fixture_server`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cross-asset-provider-quality-and-market-map-v1`
- EC2 smoke after merge to `develop`: `/api/market-map`, `/market-map`, `/api/data-health`, and services active.
