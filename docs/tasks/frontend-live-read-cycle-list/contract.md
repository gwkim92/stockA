# Task Contract

## Task

- 이름: frontend-live-read-cycle-list
- 요청: roadmap 1순위 live read completeness의 마지막 gap인 cycle list endpoint를 live Postgres read로 확장한다.
- 담당: Codex
- 날짜: 2026-05-02

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/cycles?asOfDate=...`가 fixture contract를 유지하면서 canonical Postgres state에서 live DTO로 변환될 수 있다.

## Why

- dashboard/data-health, event/theme/performance, recommendation/thesis/AI evidence/source document detail live read는 완료됐다.
- cycle list가 live가 되어야 frontend의 `/cycles` route가 fixture 없이 theme/sector cycle 상태를 추적할 수 있다.

## Scope

- 포함:
  - cycle state list live SQL/read DTO
  - live adapter routing update
  - unit tests
  - docs/task handoff 갱신
- 제외:
  - production API server
  - auth/RBAC
  - write endpoint
  - DB schema/scoring/benchmark 변경
  - frontend route redesign
  - cycle scoring formula 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-api-contract.md`
  - `docs/project-execution-roadmap.md`
  - `docs/plans/2026-05-02-frontend-live-read-cycle-list.md`
  - `docs/tasks/frontend-live-read-cycle-list/`
- 수정 금지 파일:
  - DB migrations
  - cycle scoring formula
  - benchmark/evaluation split
  - secrets/env files
  - frontend route redesign

## Verification Commands

- 검증에 사용할 명령:

  - `python3 -m py_compile src/stockanalysis/frontend/live_adapter.py tests/test_frontend_live_adapter.py`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`
  - `bash scripts/verify_frontend_live_read_adapter.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-cycle-list`
  - `rg -n "\[[A-Z_]+\]" AGENTS.md docs -S`
  - `git diff --check`

## Deliverables

- 필수 결과물:
  - cycle state list live DTO
  - tests
  - docs/task handoff/review

## Completion Criteria

- [x] `/api/cycles?asOfDate=...` live response matches frontend contract shape.
- [x] existing live responses keep passing.
- [x] unsupported endpoints still reject in live source and fixture fallback in auto.
- [x] harness verification passes.

## Risks

- strategy/universe metadata is indirect for cycle snapshots; adapter should use latest universe batch when available and stable defaults otherwise.
- actual external Postgres runtime smoke remains separate from this contract-shape slice.
