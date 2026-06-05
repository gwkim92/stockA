# Task Contract

## Task Request

- name: `free-api-cross-asset-news-cycle-integration-v1`
- request: 무료 사용량 안에서 주식 지수, 섹터 ETF, 금·은, 원유·가스, 구리, 달러, 금리, 변동성, 신용, crypto 유동성 지표를 수집하고 뉴스 AI 분석·거시 사이클·섹터/테마 사이클·종목 사이클·추천 근거에 연결한다.

## Objective

무료 사용량 안에서 주식 지수, 섹터 ETF, 금리, 달러, 원자재, 변동성, 신용, crypto 유동성 지표를 canonical DB에 저장하고 뉴스·사이클·추천 근거에 연결할 수 있는 backend foundation을 만든다.

## Goal

- goal: `stockanalysis-operations` backend CLI가 무료 provider registry, cross-asset indicator observation sync, deterministic regime snapshot, 뉴스-지표 linkage, zero-weight recommendation components를 생성할 수 있고 `/api/data-health`가 해당 상태를 read-only로 노출한다.

## Scope

- FRED, CBOE CSV, Twelve Data 중심 provider registry를 만든다.
- Alpha Vantage는 신규 primary provider에서 제외한다.
- 새 canonical tables를 추가한다.
- 기존 FRED macro default series를 cross-asset 분석에 필요한 지표로 확장한다.
- `stockanalysis-operations` CLI에 registry, indicator ingest, regime snapshot, news linkage, recommendation component runner를 추가한다.
- `stockanalysis-operations` CLI에 CBOE CSV/Twelve Data direct provider fetch runner를 추가한다.
- `data-health`에 cross-asset market regime 상태를 노출한다.
- 추천 component는 저장만 하고 weight는 모두 `0.0000`으로 둔다.

## Mutable Surface

- mutable surface:
  - `db/migrations/0030_cross_asset_market_indicators.sql`
  - `src/stockanalysis/ingest/macro/defaults.py`
  - `src/stockanalysis/operations/cross_asset_market.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/operating_data_profile_scheduler.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_cross_asset_market.py`
  - `tests/test_operating_data_profile_scheduler.py`
  - `docs/tasks/free-api-cross-asset-news-cycle-integration-v1/*`

## Non-Goals

- 실거래, broker submit, 주문 생성은 하지 않는다.
- 추천 total score, rank, benchmark, portfolio position은 바꾸지 않는다.
- 유료 provider, 외부 vector DB, Neo4j, managed graph/RAG 서비스는 도입하지 않는다.
- intraday 고빈도 시세는 이번 범위에서 제외한다.

## Implementation Plan

1. `market.market_indicator`, `market.market_indicator_observation`, `signal.market_indicator_snapshot`, `signal.cross_asset_regime_snapshot`, `event.news_indicator_link`, `signal.cross_asset_cycle_impact` migration 추가.
2. FRED 기본 series 확장.
3. `stockanalysis.operations.cross_asset_market` module 추가.
4. `stockanalysis-operations` CLI subcommands 추가.
5. operating-data cadence/profile에 cross-asset daily sequence 추가.
6. `/api/data-health` payload에 cross-asset 요약 추가.
7. DB 없는 unit test로 provider 정책, SQL, deterministic regime classifier, zero-weight boundary 검증.

## Safety Boundaries

- stale 지표는 추정값으로 채우지 않고 stale/missing으로 표시한다.
- 뉴스와 지표 shock 연결은 causal claim이 아니라 temporal evidence candidate다.
- 추천 component weight는 outcome 검증 전까지 0으로 유지한다.
- `broker_submit_allowed=false`, `order_boundary=read_only_no_order`를 유지한다.

## Verification

- verification command: `PYTHONPATH=src python3 -m unittest tests/test_cross_asset_market.py`
- verification command: `PYTHONPATH=src python3 -m compileall src tests`
- verification command: `PYTHONPATH=src python3 -m stockanalysis.operations.cli free-provider-capacity-registry-run --dry-run`
- verification command: `PYTHONPATH=src python3 -m stockanalysis.operations.cli cross-asset-indicator-provider-fetch-run --as-of-date 2026-06-05 --dry-run`
- verification command: `PYTHONPATH=src python3 -m stockanalysis.operations.cli cross-asset-regime-snapshot-run --as-of-date 2026-06-05 --dry-run`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task free-api-cross-asset-news-cycle-integration-v1`
