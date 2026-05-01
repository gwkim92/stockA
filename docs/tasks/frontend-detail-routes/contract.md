# Task Contract

## Task

- 이름: frontend-detail-routes
- 요청: fixture server DTO를 사용하는 recommendation, thesis, portfolio coverage detail routes를 `apps/web`에 추가한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `apps/web`에서 `/recommendations/AAPL-2024-11-01`, `/theses/AAPL-bootstrap-v1`, `/portfolio/coverage`가 fixture payload를 읽고 read-only detail view를 렌더링한다.

## Scope

- 포함:
  - typed DTO 확장
  - frontend API client 확장
  - 3개 detail route 추가
  - navigation link 보강
  - detail route verification script
  - docs/task handoff 갱신
- 제외:
  - write endpoint
  - live DB read adapter
  - auth/RBAC
  - AI evidence route
  - browser visual QA

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/`
  - `apps/web/src/lib/`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/frontend-detail-routes/`
  - `docs/apps-web-scaffold.md`
  - `docs/frontend-architecture.md`
  - `docs/verification-plan.md`
  - `scripts/verify_frontend_detail_routes.sh`
- 수정 금지 파일:
  - DB migrations
  - secrets
  - live trading integrations
- 검증에 사용할 명령:
  - `bash -n scripts/verify_frontend_detail_routes.sh`
  - `bash scripts/verify_frontend_detail_routes.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-detail-routes`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Completion Criteria

- [x] recommendation detail route가 fixture recommendation DTO를 렌더링한다.
- [x] thesis detail route가 fixture thesis DTO를 렌더링한다.
- [x] portfolio coverage route가 fixture portfolio coverage DTO를 렌더링한다.
- [x] routes are read-only and server-rendered.
- [x] verification script가 Next build와 route smoke를 통과한다.
- [x] 하네스 검증이 통과한다.

## Risks

- fixture-only detail routes는 live freshness를 보장하지 않는다.
- dynamic params는 현재 contract examples에 있는 known fixture ids만 정상 동작한다.
