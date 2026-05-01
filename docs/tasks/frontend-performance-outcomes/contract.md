# Task Contract

## Task

- 이름: frontend-performance-outcomes
- 요청: performance outcome과 attribution 결과를 frontend fixture-backed read-only route로 추가한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `apps/web`에서 `/performance`가 fixture payload를 읽고, 추천 outcome, benchmark 대비 alpha, attribution component, coverage gate를 함께 검토할 수 있다.

## Scope

- 포함:
  - frontend API contract에 performance outcome DTO 추가
  - fixture example 추가
  - frontend API client/types 확장
  - `/performance` route 추가
  - top navigation에 performance route 추가
  - verification scripts/tests/docs 갱신
- 제외:
  - performance/outcome DB 산식 변경
  - benchmark 기준 변경
  - live DB read adapter
  - auth/RBAC
  - AI 요약 생성 또는 투자 추천 판단 변경

## Mutable Surface

- 수정 가능한 파일:
  - `docs/api/frontend/`
  - `docs/frontend-api-contract.md`
  - `docs/frontend-architecture.md`
  - `docs/apps-web-scaffold.md`
  - `docs/verification-plan.md`
  - `docs/tasks/frontend-performance-outcomes/`
  - `apps/web/src/app/`
  - `apps/web/src/lib/`
  - `scripts/verify_frontend_api_contract.sh`
  - `scripts/verify_frontend_api_adapter.sh`
  - `scripts/verify_frontend_fixture_server.sh`
  - `scripts/verify_frontend_detail_routes.sh`
  - `tests/test_frontend_api_adapter.py`
  - `tests/test_frontend_fixture_server.py`
- 수정 금지 파일:
  - DB migrations
  - performance/outcome calculation modules
  - benchmark/evaluation semantics
  - secrets
  - broker/trading integrations

- 검증에 사용할 명령:
  - `npm run typecheck` in `apps/web`
  - `bash scripts/verify_frontend_api_contract.sh`
  - `bash scripts/verify_frontend_fixture_server.sh`
  - `bash scripts/verify_frontend_detail_routes.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-performance-outcomes`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Completion Criteria

- [x] Performance outcome API fixture is registered in `contract-index.json`.
- [x] `/performance` renders recommendation outcome, alpha, benchmark, attribution components, and coverage gates.
- [x] Route links back to recommendation, thesis, coverage, and theme context where available.
- [x] verification scripts/tests cover the new API endpoint and route.
- [x] AWH readiness checks pass.

## Risks

- Current payload is fixture-only.
- Performance route does not prove live DB freshness.
- Attribution shown is the existing simplified v1 read model; it is not a full attribution methodology expansion.
