# Task Contract

## Task Request

- name: `fred-dollar-index-lag-policy-v1`
- request: Treat `USD_BROAD_INDEX` stale status as an official FRED publication lag policy rather than a generic provider failure.

## Objective

FRED `DTWEXBGS` refreshed successfully on EC2 but the latest official observation remains `2026-05-29` for the `2026-06-05` market-map date. This is not a local collection failure. The market map should tolerate normal official-data lag while still showing the latest observation date, no-imputation policy, and reduced confidence only after the tolerated lag window.

## Goal

- goal: `USD_BROAD_INDEX` uses a lag-tolerant FRED policy with a 10-day freshness SLA, explicit no-imputation wording, and unchanged order/recommendation guardrails.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/cross_asset_market.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_cross_asset_market.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/fred-dollar-index-lag-policy-v1/*`

## Non-Goals

- Do not add paid dollar index providers.
- Do not impute missing or delayed dollar observations.
- Do not change recommendation weights, benchmark definitions, portfolio positions, broker/order flow, or write APIs.
- Do not hide the latest observation date or source limitation from the UI/API.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cross_asset_market tests.test_frontend_live_adapter`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task fred-dollar-index-lag-policy-v1`
- EC2 smoke: refresh `DTWEXBGS`, registry, cross-asset ingest, snapshot, then verify `/api/market-map` treats `USD_BROAD_INDEX` according to the lag-tolerant policy.
