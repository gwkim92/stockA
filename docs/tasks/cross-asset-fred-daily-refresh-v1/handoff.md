# cross-asset-fred-daily-refresh-v1 Handoff

## Status

- current status: implemented locally and verified; pending commit/push/EC2 smoke.
- completed: direct FRED fetch parser, ingest-run direct FRED refresh path, API key redaction for `api_key`, unit tests, CLI/orchestrator regression tests, compileall, and diff check.

## Context

- `/market-map` stale 14개는 FRED 계열 지표였다.
- FRED API 자체는 최신값을 반환했다.
- 원인은 `cross-asset-indicator-ingest`가 FRED API를 직접 호출하지 않고 `macro.observation`을 복사하는 구조였다.

## Files Touched

- 생성:
  - `docs/tasks/cross-asset-fred-daily-refresh-v1/contract.md`
  - `docs/tasks/cross-asset-fred-daily-refresh-v1/handoff.md`
- 수정:
  - `src/stockanalysis/operations/cross_asset_market.py`
  - `tests/test_cross_asset_market.py`

## Verification

- `PYTHONPATH=src python3 -m unittest tests.test_cross_asset_market -v` 통과.
- `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli tests.test_operating_data_orchestrator -v` 통과.
- `PYTHONPATH=src python3 -m compileall -q src tests` 통과.
- `git diff --check` 통과.

## Exact Next Step

- exact next step: run AWH verify, commit/merge/push to `develop`, deploy EC2, execute cross-asset ingest and regime snapshot smoke, then verify `/api/market-map?asOfDate=2026-06-12` stale count improves.
