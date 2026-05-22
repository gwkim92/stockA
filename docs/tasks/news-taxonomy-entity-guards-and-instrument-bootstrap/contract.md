# Task Contract

## Task

- 이름: news-taxonomy-entity-guards-and-instrument-bootstrap
- 요청: 뉴스 분류/종목 연결 품질을 높이고, 명확한 티커가 있는데 `ref.instrument`에 없어서 종목 미분류가 되는 경우 안전하게 새 종목을 등록할 수 있게 한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 일반 유가/원유 뉴스가 자동으로 `XOM` 직접 종목 뉴스로 붙지 않는다.
  - 일반 AI/고용/노동 뉴스가 AI 반도체 사이클로 과잉 분류되지 않는다.
  - 뉴스 제목/요약의 명시적 티커 패턴을 보수적으로 감지한다.
  - 감지된 티커가 canonical instrument에 없으면 SEC company tickers universe에서 검증된 경우에만 신규 instrument를 bootstrap할 수 있다.
  - AI가 말한 미확인 티커만으로는 instrument를 만들지 않는다.
  - 거시/시장 뉴스는 비싼 회사명 alias lookup을 수행하지 않아 enrichment가 멈춘 것처럼 느려지지 않는다.

## Scope

- 포함:
  - 뉴스 rule taxonomy guard 보강
  - explicit ticker detection 추가
  - SEC-verified missing instrument bootstrap runner/CLI 추가
  - 관련 unit tests 추가
  - EC2에서 실제 missing instrument bootstrap smoke 실행
- 제외:
  - placeholder-only instrument 생성
  - 유료 provider 도입
  - DB schema 변경
  - 추천 점수 산식 변경
  - broker/live order flow 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/enrichment.py`
  - `src/stockanalysis/ingest/news/sql.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `apps/web/src/lib/korean-labels.ts`
  - `tests/test_news_rss_enrichment.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/test_operating_data_orchestrator.py`
  - `docs/tasks/news-taxonomy-entity-guards-and-instrument-bootstrap/*`
- 수정 금지 파일:
  - `.env`
  - DB migrations/schema
  - scheduler deployment files
  - live broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_enrichment tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence -v`
  - `cd apps/web && npm run typecheck`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-taxonomy-entity-guards-and-instrument-bootstrap`

## Done Criteria

- [x] XOM oil-price direct mapping guard test가 통과한다.
- [x] AI labor/productivity theme classification test가 통과한다.
- [x] explicit ticker detection test가 통과한다.
- [x] SEC-verified missing instrument bootstrap test가 통과한다.
- [x] macro/news-only item은 company alias lookup을 건너뛰는 test가 통과한다.
- [x] CLI smoke/test가 통과한다.
- [ ] EC2 smoke에서 신규/누락 instrument bootstrap이 안전하게 실행된다.
