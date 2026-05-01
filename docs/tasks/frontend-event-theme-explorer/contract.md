# Task Contract

## Task

- 이름: frontend-event-theme-explorer
- 요청: cycle state에서 이어지는 event list와 theme detail explorer를 fixture-backed frontend route로 추가한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `apps/web`에서 `/events`와 `/themes/ANNUAL_REPORTING`이 fixture payload를 읽고, 이벤트/테마/사이클/증거/종목 연결을 read-only로 탐색할 수 있다.

## Scope

- 포함:
  - frontend API contract에 event list와 theme detail DTO 추가
  - fixture examples 추가
  - frontend API client/types 확장
  - `/events` route 추가
  - `/themes/[themeKey]` route 추가
  - `/cycles`에서 theme detail로 이동하는 링크 추가
  - verification scripts/tests/docs 갱신
- 제외:
  - live DB read adapter
  - event write/mutation
  - AI prompt 실행 또는 재생성
  - auth/RBAC
  - 투자 추천 로직 변경

## Mutable Surface

- 수정 가능한 파일:
  - `docs/api/frontend/`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-architecture.md`
  - `docs/apps-web-scaffold.md`
  - `docs/verification-plan.md`
  - `docs/tasks/frontend-event-theme-explorer/`
  - `apps/web/src/app/`
  - `apps/web/src/lib/`
  - `scripts/verify_frontend_api_contract.sh`
  - `scripts/verify_frontend_detail_routes.sh`
  - `scripts/verify_frontend_fixture_server.sh`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_fixture_server.py`
- 수정 금지 파일:
  - DB migrations
  - secrets
  - live trading integrations
  - scoring/evaluation benchmark

- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_detail_routes.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-event-theme-explorer`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Completion Criteria

- [x] Event list API fixture is registered in `contract-index.json`.
- [x] Theme detail API fixture is registered in `contract-index.json`.
- [x] `/events` renders event list with linked AI evidence, source document, and theme detail.
- [x] `/themes/ANNUAL_REPORTING` renders cycle state, linked instruments, evidence events, and feature snapshot.
- [x] `/cycles` links each known theme to theme detail when supported.
- [x] verification script covers the new routes.
- [x] AWH readiness checks pass.

## Risks

- Current payload is fixture-only and supports one full theme detail route.
- Event/theme explorer does not prove live DB freshness.
- Broader event filtering, pagination, and auth remain later tasks.
