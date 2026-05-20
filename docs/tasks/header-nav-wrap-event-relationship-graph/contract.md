# Task Contract

## Task

- 이름: header-nav-wrap-event-relationship-graph
- 요청: 헤더 내비게이션이 잘리지 않게 고치고, 다음 순서인 이벤트 관계 그래프 표시를 진행한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 헤더 내비게이션은 항목이 많아도 가로로 잘리지 않고 줄바꿈된다.
  - `/events`와 `/intelligence`에서 이벤트끼리 어떤 관계가 있는지 최소 그래프 형태로 보인다.
  - 관계는 기존 read-only 이벤트/문서/테마/종목 데이터를 기반으로 산출한다.
  - 신규 뉴스 provider 호출, scoring 변경, broker write, 주문 실행은 하지 않는다.

## Scope

- `apps/web/src/app/globals.css` 헤더 내비게이션 wrapping 수정.
- Event DTO에 `related_events` read model 추가.
- `src/stockanalysis/frontend/live_adapter.py` 이벤트 목록 SQL/payload에 관계 후보 추가.
- `docs/api/frontend/examples/event-list.json` fixture 갱신.
- `/events`, `/intelligence` 화면에 관계 표시 추가.
- 타입/테스트/하네스 문서 갱신.

## Boundaries

- 실시간 뉴스 수집기는 이번 slice에서 구현하지 않는다.
- DB schema, recommendation scoring, benchmark, evaluation split을 바꾸지 않는다.
- write endpoint, broker execution, kill switch 변경을 하지 않는다.
- secret, token, DB URL을 출력하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/globals.css`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/lib/types.ts`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `docs/api/frontend/examples/event-list.json`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/plans/2026-05-19-header-nav-wrap-event-relationship-graph.md`
  - `docs/tasks/header-nav-wrap-event-relationship-graph/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_api_adapter tests.test_frontend_live_adapter`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `curl -fsS -o /private/tmp/stockanalysis-runtime/intelligence.html -w '%{http_code}' http://127.0.0.1:3001/intelligence`
  - `curl -fsS -o /private/tmp/stockanalysis-runtime/events.html -w '%{http_code}' http://127.0.0.1:3001/events`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task header-nav-wrap-event-relationship-graph`
  - `git diff --check`

## Done Criteria

- [x] header nav no longer depends on hidden horizontal scrolling.
- [x] event payload includes relationship candidates.
- [x] `/events` renders relationship chips/cards.
- [x] `/intelligence` renders relationship evidence in the trace flow.
- [x] required verification passes.
