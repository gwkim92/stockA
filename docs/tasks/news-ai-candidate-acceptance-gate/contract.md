# Task Contract

## Task

- 이름: news-ai-candidate-acceptance-gate
- 요청: AI가 실행됐다는 이유만으로 저품질 뉴스 후보가 `news_event_candidate`로 화면과 추천 입력 후보에 남지 않게 한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `news-rss-ai-extract-run`은 검증된 theme/instrument impact가 하나도 없으면 accepted `news_event_candidate` artifact를 만들지 않는다.
  - 검증 실패 후보는 감사용 `news_event_candidate_rejected` artifact로 저장되어 재실행 중복 호출을 막는다.
  - `/events?evidenceType=news_event_candidate`와 `/ai-evidence` 후보 화면은 기존 저신뢰 무종목 일반 뉴스 artifact를 숨긴다.
  - 공식 macro/Fed/SEC 무종목 후보와 검증된 직접 종목 후보는 기존처럼 유지된다.

## Scope

- 포함:
  - news AI runner artifact acceptance gate
  - rejected artifact type 저장과 중복 호출 방지
  - frontend live event list 품질 필터 보강
  - focused tests, task handoff, EC2 smoke
- 제외:
  - DB migration
  - 기존 artifact 삭제
  - 추천 점수 산식 변경
  - scheduler cadence 변경
  - 유료 뉴스 API, 외부 RAG, broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/ai_extract.py`
  - `src/stockanalysis/ingest/news/sql.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_news_rss_ai_extract.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/news-ai-candidate-acceptance-gate/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler units/timers
  - recommendation scoring weights
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_news_rss_ai_extract tests.test_frontend_live_adapter -v`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-candidate-acceptance-gate`
  - EC2 dry-run/execute smoke for `news-rss-ai-extract-run`
  - EC2 API/browser smoke for `/events`, `/ai-evidence`, `/api/data-health`

## Done Criteria

- [ ] No validated impacts means `news_event_candidate_rejected`, not accepted `news_event_candidate`.
- [ ] Existing rejected artifacts prevent repeated LLM calls for the same request hash.
- [ ] Candidate screens suppress existing no-symbol low-confidence general-news artifacts.
- [ ] Local verification and AWH pass.
- [ ] EC2 deploy and smoke pass.
