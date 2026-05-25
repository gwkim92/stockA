# Session Handoff

## Current Status

- 완료: sector classification seed와 seed integrity tests를 추가했고, 로컬 단위/compile/seed bootstrap/AWH 및 EC2 seed/API/route smoke를 통과했다.

## Implementation Notes

- 원인: 포트폴리오 concentration API는 정상적으로 `ref.instrument_classification_membership`를 읽지만, 현재 seed에는 `node_type='sector'` membership이 없다.
- 접근:
  - schema 변경 없이 Postgres ontology-lite seed를 보강한다.
  - 첫 범위는 현재 포트폴리오/분석에 등장한 core US symbols만 다룬다.
  - 전체 GICS universe 구축은 후속 task로 둔다.
- 추가된 seed:
  - `db/seeds/0005_sector_classification_seed.sql`
  - sector nodes: `BROAD_US_EQUITY`, `TECHNOLOGY`, `CONSUMER_DISCRETIONARY`, `ENERGY`, `FINANCIALS`, `FIXED_INCOME`
  - sector memberships: `AAPL`, `MSFT`, `NVDA`, `TSLA`, `XOM`, `SPY`, `QQQ`, `TLT`, `XLF`, `XLE`, `QUBT`, `BABA`
  - AAPL/BABA instrument도 fresh seed에서 보장한다.
- 경계:
  - 추천 weight는 바꾸지 않는다.
  - broker/order submit은 건드리지 않는다.
  - sector seed는 read-only 분석/위험예산 입력이다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_sector_classification_seed tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `bash scripts/verify_seed_bootstrap.sh`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task sector-classification-enrichment-v1`
- Passed on EC2: pulled `239bd48`.
- Passed on EC2 seed apply: `docker exec -i stockanalysis-postgres psql -U stockanalysis -d stockanalysis -v ON_ERROR_STOP=1 < db/seeds/0005_sector_classification_seed.sql`.
- Passed on EC2 DB count: sector memberships count `12`.
- Passed on EC2 API: `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25` returned effective `as_of=2026-05-23`, risk status `needs_position_review`, concentration status `needs_concentration_review`, sector exposure count `2`, top sector `TECHNOLOGY`, theme exposure count `4`, unclassified weight `0.0`.
- Passed on EC2 API: review reasons no longer included `sector_classification_missing`; reasons were `over_single_position_limit:MSFT`, `over_single_position_limit:TSLA`, `sector_over_limit:TECHNOLOGY`, `theme_over_limit:US_MARKET_BREADTH`.
- Passed on EC2 route smoke: `/portfolio/coverage` rendered `섹터·테마 집중도`, `TECHNOLOGY`, `미분류 비중`, `0%`, and no `sector_classification_missing`.

## Exact Next Step

- exact next step: 다음 작업은 `frontend-equity-research-experience-v2`로 종목/추천 상세를 전문 리서치 리포트 순서로 재정리하거나, `industry-competitive-positioning-v1`로 sector보다 한 단계 아래 산업/피어 경쟁구조를 추가한다.
