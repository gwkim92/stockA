# Task Contract

## Task Request

- name: `cross-asset-etf-watchlist-price-refresh-v1`
- request: cross-asset regime 입력에서 missing으로 남은 지수/섹터/채권 ETF 지표를 무료 Twelve Data 예산 안에서 자동 수집한다.

## Objective

`cross-asset-daily` profile이 `SPY`, `QQQ`, `IWM`, `DIA`, 섹터 ETF, `TLT`, `HYG`, `LQD` 가격을 먼저 `market.daily_price_bar`에 보강한 뒤 기존 `cross-asset-indicator-ingest`가 이를 `market.market_indicator_observation`으로 동기화하게 만든다.

## Goal

- goal: `cross-asset-daily` profile이 cross-asset ETF/rates/credit ETF 가격 refresh step을 indicator sync 전에 실행하고, missing ETF 지표를 줄일 수 있는 repo-outside watchlist와 artifact evidence를 생성한다.

## Scope

- cross-asset indicator registry에서 `instrument_symbol`이 있는 Twelve Data 지표를 watchlist로 자동 생성한다.
- `cross-asset-daily` profile에 `cross-asset-market-price-refresh` step을 추가한다.
- 기존 `market-price-free-backfill-run`을 재사용한다.
- free-tier budget ledger와 `--skip-if-fresh`를 유지한다.
- 개별 symbol 실패는 JSON artifact에 남기되 profile 전체를 막지 않는다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/cross_asset_market.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/cadence.py`
  - `tests/test_cross_asset_market.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/cross-asset-etf-watchlist-price-refresh-v1/*`

## Non-Goals

- 추천 weight, score, rank는 변경하지 않는다.
- broker/order flow는 변경하지 않는다.
- 유료 provider를 추가하지 않는다.
- 원자재/FX symbol fallback 문제(`XAG_USD` HTTP 404)는 이번 task에서 해결하지 않는다.
- `/market-map` UI는 다음 task로 둔다.

## Verification

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_cross_asset_market tests.test_operating_data_orchestrator tests.test_operating_data_profile_scheduler`
- verification command: `PYTHONPATH=src python3 -m compileall src tests`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cross-asset-etf-watchlist-price-refresh-v1`
- EC2 smoke: `operating-data-run --profile cross-asset-daily --execute` after deploy, then inspect `/api/data-health.cross_asset_market_regime`.
