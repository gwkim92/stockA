# Task Contract

## Task

- 이름: news-ai-candidate-quality-gate
- 요청: UI에서 숨긴 저품질 뉴스 후보를 백엔드 `news_event_candidate` 생성 단계에서 줄인다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 무종목 `marketwatch-topstories` 개인 재무/일반 뉴스가 AI 후보 생성 대상에서 제외된다.
  - SQL 후보 조회와 Python 후보 loader가 같은 품질 게이트를 공유한다.
  - 제외된 후보는 LLM 호출, `ai.model_invocation`, `news_event_candidate` artifact를 만들지 않는다.
  - 공식 거시/SEC/Fed 뉴스와 명확한 종목 뉴스는 기존처럼 후보가 될 수 있다.

## Scope

- 포함:
  - `news-rss-ai-extract-run` 후보 선택 품질 게이트
  - 무종목/unknown symbol 처리 통일
  - focused unit tests
  - task handoff와 검증 기록
- 제외:
  - DB migration
  - 기존 artifact 삭제
  - 추천 scoring 변경
  - scheduler cadence 변경
  - 유료 뉴스 API, 외부 RAG, broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/ai_extract.py`
  - `src/stockanalysis/ingest/news/sql.py`
  - `tests/test_news_rss_ai_extract.py`
  - `docs/tasks/news-ai-candidate-quality-gate/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler units
  - recommendation scoring weights
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_ai_extract`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-candidate-quality-gate`
  - EC2 dry-run smoke for `news-rss-ai-extract-run`

## Done Criteria

- [x] SQL candidate query excludes no-symbol MarketWatch topstories.
- [x] Python loader filters no-symbol MarketWatch topstories even if supplied by an older query/fixture.
- [x] Tests prove noisy candidates are skipped before provider invocation.
- [x] Local verification and AWH pass.
- [ ] EC2 dry-run shows candidate selection still works without generating noisy topstory candidates.
