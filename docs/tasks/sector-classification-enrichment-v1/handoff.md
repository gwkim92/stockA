# Session Handoff

## Current Status

- 완료: sector classification seed와 seed integrity tests를 추가했고, 로컬 단위/compile/seed bootstrap/AWH 검증을 통과했다.

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

## Exact Next Step

- exact next step: Git commit/push 후 EC2에 fast-forward 배포하고, `db/seeds/0005_sector_classification_seed.sql`를 EC2 DB에 적용한 뒤 `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25`에서 sector exposure count가 0이 아닌지 smoke 검증한다.
