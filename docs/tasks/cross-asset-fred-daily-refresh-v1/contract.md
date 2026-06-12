# Task Contract

## Task

- 이름: cross-asset-fred-daily-refresh-v1
- 요청: cross-asset daily에서 오래된 FRED 지표가 발생하는 원인을 해소한다.
- 담당: Codex
- 날짜: 2026-06-12

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `cross-asset-indicator-ingest-run`이 FRED 계열 시장 지표를 macro weekly refresh에 의존하지 않고 직접 최신 fetch/upsert한 뒤 market indicator snapshot을 만들 수 있어야 한다.

## Why

- `/market-map`의 오래된 지표 14개는 FRED API 원천 지연이 아니라, cross-asset ingest가 `macro.observation`에 이미 들어온 값을 복사하는 구조 때문에 발생했다.
- daily 시장 지도는 금리, 달러, 원유, VIX, 신용 스프레드 같은 FRED 계열 지표를 매일 직접 갱신해야 한다.

## Scope

- 포함:
  - cross-asset ingest 내부 FRED direct fetch 추가
  - FRED observation parser와 market indicator observation upsert
  - unit tests
  - EC2 smoke로 stale count 개선 확인
  - task handoff 갱신
- 제외:
  - schema 변경
  - 추천 scoring weight 변경
  - broker/order flow
  - 유료 provider 추가
  - macro weekly 파이프라인 구조 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/cross_asset_market.py`
  - `tests/test_cross_asset_market.py`
  - `docs/tasks/cross-asset-fred-daily-refresh-v1/`
- 수정 금지:
  - repo 밖 env/secrets
  - DB migrations
  - recommendation weight/evaluation split
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
- `PYTHONPATH=src python3 -m unittest tests.test_cross_asset_market -v`
- `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli tests.test_operating_data_orchestrator -v`
- `PYTHONPATH=src python3 -m compileall -q src tests`
- `git diff --check`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task cross-asset-fred-daily-refresh-v1`
- EC2 smoke:
  - `stockanalysis-operations cross-asset-indicator-ingest-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-06-12 --execute`
  - `stockanalysis-operations cross-asset-regime-snapshot-run --env-file /opt/stockanalysis/runtime/data-operations.env --as-of-date 2026-06-12 --execute`
  - `/api/market-map?asOfDate=2026-06-12` stale count 확인

## Completion Criteria

- [ ] FRED API에서 최신 observations를 직접 읽어 `market.market_indicator_observation`에 upsert한다.
- [ ] API key는 output/evidence에 노출되지 않는다.
- [ ] 기존 macro/price sync 경로는 유지된다.
- [ ] unit/compile/diff/AWH 검증이 통과한다.
- [ ] EC2 smoke에서 오래된 FRED 지표 수가 감소하거나, 남은 stale이 실제 FRED 최신 관측일/SLA 기준임을 확인한다.
