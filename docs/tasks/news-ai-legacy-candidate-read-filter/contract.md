# Task Contract

## Task

- 이름: news-ai-legacy-candidate-read-filter
- 요청: 이미 생성된 저신호 `news_event_candidate` artifact가 기본 AI 후보 목록에 계속 보이는 문제를 read model에서 줄인다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/events?evidenceType=news_event_candidate`는 직접 종목 없는 `rss_news:marketwatch-topstories` 후보를 기본 후보 목록에서 제외한다.
  - 기존 artifact row는 삭제하지 않는다.
  - `/events` raw 원장과 직접 종목이 붙은 MarketWatch 후보는 계속 확인 가능하다.
  - `/ai-evidence` 목록은 read filter를 통해 더 이상 저신호 무종목 topstory 후보를 기본 노출하지 않는다.

## Scope

- 포함:
  - frontend live adapter event list SQL filter 보강
  - focused SQL regression test
  - task handoff와 검증 기록
- 제외:
  - DB migration
  - historical artifact delete/update
  - scheduler cadence 변경
  - 추천 점수 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/news-ai-legacy-candidate-read-filter/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler units
  - recommendation scoring weights
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task news-ai-legacy-candidate-read-filter`
  - EC2 `/api/events?evidenceType=news_event_candidate` smoke

## Done Criteria

- [x] SQL filter excludes no-symbol MarketWatch topstories only when listing `news_event_candidate`.
- [x] Direct-symbol MarketWatch candidates remain eligible.
- [x] Existing raw ledger behavior is not changed.
- [x] Local verification and AWH pass.
- [ ] EC2 API smoke confirms candidate list excludes no-symbol topstory shape.
