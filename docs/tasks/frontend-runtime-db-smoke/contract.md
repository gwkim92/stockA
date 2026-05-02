# Task Contract

## Task

- 이름: frontend-runtime-db-smoke
- 요청: runtime boundary 이후 실제 Postgres state를 읽는 HTTP live smoke를 추가한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: frontend read-only HTTP runtime이 `source=live`와 production-profile guard로 실행되어 disposable Postgres에 적재된 canonical state를 대표 DTO로 반환한다.

## Why

- fixture server와 live adapter unit tests만으로는 HTTP runtime, runtime policy, `STOCKANALYSIS_PSQL_COMMAND`, 실제 DB state가 함께 동작하는지 증명하지 못한다.
- write API나 connection pooling을 논의하기 전에 read-only live boundary가 실제 DB 위에서 닫혀야 한다.

## In Scope

- Add a disposable Docker Postgres verification script.
- Apply existing migrations and seed files.
- Run existing deterministic fixture data pipelines needed for representative frontend live reads.
- Start the existing frontend HTTP runtime with `source=live`.
- Use production runtime guards: explicit CORS origin, `read-token` auth, and `STOCKANALYSIS_PSQL_COMMAND`.
- Verify public health, unauthorized read rejection, and authorized DB-backed API reads over HTTP.
- Update roadmap, verification, and runtime docs.

## Out Of Scope

- No DB schema changes.
- No benchmark, scoring, or evaluation split changes.
- No write API.
- No full auth/RBAC, session, actor identity, or audit-write model.
- No connection pooling or managed API server framework.
- No production deployment config.
- No broker/order/trading automation.

## Mutable Surface

- 수정 가능한 파일:
  - `scripts/verify_frontend_runtime_db_smoke.sh`
  - `docs/frontend-runtime-db-smoke.md`
  - `docs/frontend-api-runtime-boundary.md`
  - `docs/frontend-architecture.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-03-frontend-runtime-db-smoke.md`
  - `docs/tasks/frontend-runtime-db-smoke/`
- 수정 금지 파일:
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - secrets/env files
  - write endpoint implementation

## Required State When Complete

- [ ] `scripts/verify_frontend_runtime_db_smoke.sh` exists and is executable.
- [ ] The script starts a disposable Postgres container and cleans it up.
- [ ] The script starts the frontend HTTP runtime against live Postgres state.
- [ ] `/__health` returns safe runtime metadata without auth.
- [ ] `/api/dashboard/today` rejects missing bearer token when auth is enabled.
- [ ] Authorized live HTTP reads return database-backed DTOs for representative endpoints.
- [ ] Docs identify the next remaining API runtime work after this smoke.
- [ ] The task handoff and review files contain verification evidence and residual risks.

## Verification Commands

- 검증에 사용할 명령:
  - `bash scripts/verify_frontend_runtime_db_smoke.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-runtime-db-smoke`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `rg -n "\[[A-Z_]+\]" AGENTS.md docs -S`
  - `git diff --check`

## Risk Notes

- This is a smoke test, not a production server implementation.
- The runtime still shells out through `psql`; connection pooling is intentionally deferred.
- `read-token` is a boundary seam, not full user identity or RBAC.
