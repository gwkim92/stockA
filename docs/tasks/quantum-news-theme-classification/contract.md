# Task Contract

## Task

- 이름: quantum-news-theme-classification
- 요청: `Quantum stocks soar as the Trump administration looks to be buying in` 같은 양자컴퓨팅 뉴스가 에너지 또는 너무 넓은 시장 흐름으로 보이지 않게 분류 체계와 클러스터링을 고친다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 양자컴퓨팅/정부 정책 수혜 뉴스는 `QUANTUM_COMPUTING_POLICY` 테마로 분류된다.
  - `QUBT` 같은 명확한 양자 종목은 rule enrichment에서 직접 종목 후보로 잡힌다.
  - `US_MARKET_BREADTH` 클러스터도 story split 대상이 되어 무관한 광범위 뉴스가 한 덩어리로 묶이는 현상이 줄어든다.
  - 기존 잘못된 현재 DB 데이터는 EC2에서 새 분류 기준으로 보정한다.

## Scope

- 포함:
  - 뉴스 RSS classification bootstrap에 양자 테마 추가
  - rule-based theme/instrument keyword 보강
  - broad story cluster split 대상 확장
  - Korean label 추가
  - unit tests 추가
  - EC2 current data repair
- 제외:
  - DB schema 변경
  - 추천 점수 산식 변경
  - 실거래/broker 로직 변경
  - 유료 provider 도입

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/enrichment.py`
  - `src/stockanalysis/ingest/news/sql.py`
  - `src/stockanalysis/ingest/news/cluster_evidence.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/korean-labels.ts`
  - `db/seeds/0003_factor_exposure_seed.sql`
  - `tests/test_news_rss_enrichment.py`
  - `tests/test_news_rss_cluster_evidence.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/quantum-news-theme-classification/*`
- 수정 금지 파일:
  - `.env`
  - DB migrations/schema
  - scheduler cadence
  - broker/live order submit logic

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_enrichment tests.test_news_rss_cluster_evidence tests.test_frontend_live_adapter -v`
  - `cd apps/web && npm run typecheck`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task quantum-news-theme-classification`

## Done Criteria

- [ ] 양자 뉴스 rule classification test가 통과한다.
- [ ] `US_MARKET_BREADTH` story split test가 통과한다.
- [ ] frontend cluster SQL이 `US_MARKET_BREADTH` story split theme cluster를 숨긴다.
- [ ] EC2 데이터에서 해당 Quantum 뉴스가 양자 테마로 보정된다.
- [ ] 검증이 통과한다.
