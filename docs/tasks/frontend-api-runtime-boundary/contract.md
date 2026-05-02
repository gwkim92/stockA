# Task Contract

## Task

- 이름: frontend-api-runtime-boundary
- 요청: initial frontend contract live read completeness 이후 production API runtime boundary를 설계하고 최소 구현한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: local read-only HTTP runtime이 production-facing boundary policy를 명시적으로 적용하고, non-local/prod 실행은 auth/CORS/DB source guard 없이는 시작되지 않는다.

## Why

- 모든 초기 frontend contract endpoint는 fixture/live adapter로 읽을 수 있게 됐다.
- 다음 단계에서 실제 배포나 BFF를 붙이려면 브라우저 DB 접근 금지, auth/RBAC seam, source mode, CORS, error leakage 경계를 먼저 고정해야 한다.

## Scope

- 포함:
  - runtime profile policy
  - startup guard
  - token auth seam for read endpoints
  - CORS origin policy
  - health/startup metadata
  - verification script
  - docs/task handoff 갱신
- 제외:
  - full user auth/RBAC
  - write endpoint
  - broker/order flow
  - DB schema/scoring/benchmark 변경
  - production deployment
  - connection pool implementation

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/runtime_policy.py`
  - `src/stockanalysis/frontend/fixture_server.py`
  - `tests/test_frontend_fixture_server.py`
  - `scripts/verify_frontend_api_runtime_boundary.sh`
  - `docs/frontend-api-runtime-boundary.md`
  - `docs/frontend-fixture-server.md`
  - `docs/frontend-architecture.md`
  - `docs/frontend-api-adapter.md`
  - `docs/project-execution-roadmap.md`
  - `README.md`
  - `pyproject.toml`
  - `docs/plans/2026-05-03-frontend-api-runtime-boundary.md`
  - `docs/tasks/frontend-api-runtime-boundary/`
- 수정 금지 파일:
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - secrets/env files
  - write endpoint implementation

## Verification Commands

- 검증에 사용할 명령:
  - `python3 -m py_compile src/stockanalysis/frontend/runtime_policy.py src/stockanalysis/frontend/fixture_server.py tests/test_frontend_fixture_server.py`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_fixture_server -v`
  - `bash scripts/verify_frontend_fixture_server.sh`
  - `bash scripts/verify_frontend_api_runtime_boundary.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-runtime-boundary`
  - `rg -n "\[[A-Z_]+\]" AGENTS.md docs -S`
  - `git diff --check`

## Deliverables

- 필수 결과물:
  - runtime policy module
  - server integration
  - tests
  - verification script
  - docs/task handoff/review

## Completion Criteria

- [x] default fixture local behavior remains unchanged.
- [x] non-loopback local unauthenticated exposure is rejected.
- [x] production profile requires explicit allowed origin, read token auth, and DB command for live/auto source.
- [x] read-token auth blocks protected API requests without a bearer token.
- [x] health/startup metadata exposes runtime profile without leaking tokens.
- [x] docs and handoff are updated.
- [x] harness verification passes.

## Risks

- This is a boundary seam, not full auth/RBAC. Real identity, roles, sessions, audit logs, and deployment hardening still require a later task.
- `STOCKANALYSIS_PSQL_COMMAND` remains command-based for now; connection pooling is documented but not implemented in this slice.
