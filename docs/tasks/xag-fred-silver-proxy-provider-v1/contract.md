# Task Contract

## Task Request

- name: `xag-fred-silver-proxy-provider-v1`
- request: Replace the unresolved Twelve Data `XAG_USD` direct fetch gap with a no-key, scheduler-safe free provider path.

## Objective

Use an official/free source that can run unattended. Twelve Data rejected `XAG/USD`, `XAGUSD`, and `SILVER`; Stooq now requires an API key/captcha flow; FRED exposes a current daily silver-related proxy series `NASDAQQSLVO`. Use that proxy only with explicit labeling and no spot-price claim.

## Goal

- goal: `XAG_USD` no longer remains missing in `/market-map`; it is populated from FRED `NASDAQQSLVO` as a silver price proxy, with UI/API text clearly stating that it is not spot XAG/USD and should be used only as a directional silver-market input.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/cross_asset_market.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_cross_asset_market.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/xag-fred-silver-proxy-provider-v1/*`

## Non-Goals

- Do not add paid providers.
- Do not add captcha/manual provider dependencies.
- Do not change recommendation weights, benchmark definitions, portfolio positions, broker/order flow, or write APIs.
- Do not claim FRED `NASDAQQSLVO` is silver spot in USD.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cross_asset_market tests.test_frontend_live_adapter`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task xag-fred-silver-proxy-provider-v1`
- EC2 smoke: run registry, FRED ingest, snapshot, then verify `/api/market-map` has no missing `XAG_USD` and still says this is a silver proxy, not spot.
