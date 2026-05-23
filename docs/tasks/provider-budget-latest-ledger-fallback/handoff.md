# Session Handoff

## Current Status

- 상태: in_progress
- in progress: provider budget ledger가 오늘 row missing일 때 최신 기록으로 fallback하도록 수정 중이다.
- 기준일: 2026-05-23

## Investigation

- EC2 ledger path `/opt/stockanalysis/runtime/market-price-budget-ledger.json` exists.
- ledger provider is `twelve_data`.
- ledger days are `2026-05-20`, `2026-05-21`, `2026-05-22`.
- `/data-health` 기준일은 `2026-05-23`이라 오늘 row가 없고, 기존 reader는 이 경우 `day_missing` empty budget을 반환해 화면이 `0/0`으로 보인다.
- root cause: data health는 현재 날짜를 기준으로 provider budget을 조회하지만, 주말/비거래일 또는 아직 market daily가 돌지 않은 날에는 최신 ledger day를 fallback하지 않는다.

## Mutable Surface

- `src/stockanalysis/operations/market_price_free_backfill.py`
- `src/stockanalysis/frontend/live_adapter.py`
- `tests/test_market_price_free_backfill.py`
- `tests/test_frontend_live_adapter.py`
- `docs/tasks/provider-budget-latest-ledger-fallback/*`

## Exact Next Step

- exact next step: `load_market_price_provider_budget_status`에 opt-in latest-day fallback을 추가하고, live data health에서만 활성화한 뒤 단위 테스트와 EC2 smoke로 검증한다.
