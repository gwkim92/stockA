# Task Contract

## Task

- 이름: frontend-live-read-expansion
- 요청: roadmap 1순위에 따라 frontend live read 지원 범위를 dashboard/data-health부터 확장한다.
- 담당: Codex
- 날짜: 2026-05-01

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/dashboard/today`와 `/api/data-health`가 fixture contract를 유지하면서 canonical Postgres state에서 live DTO로 변환될 수 있다.

## Why

- roadmap의 1순위는 live read completeness다.
- dashboard와 data-health는 전체 운영 상태와 파이프라인 freshness를 보여주는 상위 관문이므로 가장 먼저 live가 되어야 한다.

## Scope

- 포함:
  - live dashboard state SQL/read DTO
  - live data-health SQL/read DTO
  - live adapter routing update
  - unit tests
  - verification update
  - docs/task handoff 갱신
- 제외:
  - production API server
  - auth/RBAC
  - write endpoint
  - event/theme/performance live expansion
  - DB schema/scoring/benchmark 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `scripts/verify_frontend_live_read_adapter.sh`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-api-contract.md`
  - `docs/project-execution-roadmap.md`
  - `docs/tasks/frontend-live-read-expansion/`
- 수정 금지 파일:
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - secrets/env files
  - frontend route redesign
- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_live_read_adapter.sh`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-expansion`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
  - `git diff --check`

## Deliverables

- 필수 결과물:
  - dashboard live DTO
  - data-health live DTO
  - tests
  - docs/task handoff/review

## Completion Criteria

- [x] `/api/dashboard/today` live response matches frontend contract shape.
- [x] `/api/data-health` live response matches frontend contract shape.
- [x] existing remediation/coverage live responses keep passing.
- [x] unsupported endpoints still reject in live source and fixture fallback in auto.
- [x] harness verification passes.

## Risks

- dashboard metrics are only as good as currently persisted pipeline state.
- scheduler install/readiness remains documented/static until production runtime config is introduced.
