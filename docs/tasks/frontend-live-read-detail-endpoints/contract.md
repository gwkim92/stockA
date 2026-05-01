# Task Contract

## Task

- 이름: frontend-live-read-detail-endpoints
- 요청: roadmap 1순위 live read completeness의 다음 slice로 recommendation/thesis/AI evidence/source document detail endpoint를 live Postgres read로 확장한다.
- 담당: Codex
- 날짜: 2026-05-02

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/recommendations/:id`, `/api/theses/:id`, `/api/ai-evidence/:id`, `/api/source-documents/:id`가 fixture contract를 유지하면서 canonical Postgres state에서 live DTO로 변환될 수 있다.

## Why

- dashboard, data-health, event, theme, performance live read는 완료됐다.
- 남은 주요 detail endpoint가 live가 되어야 frontend가 추천 판단, thesis, AI evidence, source document provenance를 fixture 없이 추적할 수 있다.

## Scope

- 포함:
  - recommendation detail live SQL/read DTO
  - thesis detail live SQL/read DTO
  - AI evidence detail live SQL/read DTO
  - source document detail live SQL/read DTO
  - live adapter routing update
  - unit tests
  - docs/task handoff 갱신
- 제외:
  - production API server
  - auth/RBAC
  - write endpoint
  - DB schema/scoring/benchmark 변경
  - live AI provider execution
  - raw document browser download

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-api-contract.md`
  - `docs/project-execution-roadmap.md`
  - `docs/plans/2026-05-02-frontend-live-read-detail-endpoints.md`
  - `docs/tasks/frontend-live-read-detail-endpoints/`
- 수정 금지 파일:
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - secrets/env files
  - frontend route redesign
- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_live_read_adapter.sh`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-detail-endpoints`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
  - `git diff --check`

## Deliverables

- 필수 결과물:
  - recommendation detail live DTO
  - thesis detail live DTO
  - AI evidence detail live DTO
  - source document detail live DTO
  - tests
  - docs/task handoff/review

## Completion Criteria

- [x] `/api/recommendations/:id` live response matches frontend contract shape.
- [x] `/api/theses/:id` live response matches frontend contract shape.
- [x] `/api/ai-evidence/:id` live response matches frontend contract shape.
- [x] `/api/source-documents/:id` live response matches frontend contract shape.
- [x] existing live responses keep passing.
- [x] unsupported endpoints still reject in live source and fixture fallback in auto.
- [x] harness verification passes.

## Risks

- path IDs may be fixture slugs or opaque numeric IDs; adapter must support both conservatively.
- source document raw download remains disabled until auth/RBAC exists.
