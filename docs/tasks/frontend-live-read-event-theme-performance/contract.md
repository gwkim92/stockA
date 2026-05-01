# Task Contract

## Task

- 이름: frontend-live-read-event-theme-performance
- 요청: roadmap 1순위 live read completeness의 다음 slice로 event/theme/performance endpoint를 live Postgres read로 확장한다.
- 담당: Codex
- 날짜: 2026-05-02

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/events?asOfDate=...`, `/api/themes/:themeKey?asOfDate=...`, `/api/performance/:portfolio/outcomes?measurementEndDate=...`가 fixture contract를 유지하면서 canonical Postgres state에서 live DTO로 변환될 수 있다.

## Why

- dashboard/data-health live read first slice가 완료됐다.
- 다음 운영 가치는 이벤트 provenance, 테마 cycle context, 성과/attribution feedback을 frontend가 fixture가 아닌 canonical state에서 읽는 것이다.

## Scope

- 포함:
  - event list live SQL/read DTO
  - theme detail live SQL/read DTO
  - performance outcomes live SQL/read DTO
  - live adapter routing update
  - unit tests
  - docs/task handoff 갱신
- 제외:
  - production API server
  - auth/RBAC
  - write endpoint
  - AI evidence/source document detail live expansion
  - recommendation/thesis detail live expansion
  - DB schema/scoring/benchmark 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/frontend-api-adapter.md`
  - `docs/frontend-api-contract.md`
  - `docs/project-execution-roadmap.md`
  - `docs/tasks/frontend-live-read-event-theme-performance/`
- 수정 금지 파일:
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - secrets/env files
  - frontend route redesign
- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_live_read_adapter.sh`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-event-theme-performance`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
  - `git diff --check`

## Deliverables

- 필수 결과물:
  - event list live DTO
  - theme detail live DTO
  - performance outcomes live DTO
  - tests
  - docs/task handoff/review

## Completion Criteria

- [x] `/api/events?asOfDate=...` live response matches frontend contract shape.
- [x] `/api/themes/:themeKey?asOfDate=...` live response matches frontend contract shape.
- [x] `/api/performance/:portfolio/outcomes?measurementEndDate=...` live response matches frontend contract shape.
- [x] dashboard/data-health/remediation/coverage live responses keep passing.
- [x] unsupported endpoints still reject in live source and fixture fallback in auto.
- [x] harness verification passes.

## Risks

- event/theme DTO는 AI evidence/source document detail endpoint가 아직 live가 아니므로 IDs/links만 먼저 노출한다.
- performance DTO는 기존 benchmark/outcome/attribution 데이터를 읽기만 하고 계산 방식은 바꾸지 않는다.
