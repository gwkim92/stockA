# Task Contract

## Task

- 이름: frontend-api-server-framework-decision
- 요청: production-candidate frontend API server framework를 FastAPI로 고정하고 read-only live API server를 구현한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: FastAPI + Uvicorn + psycopg pool 기반 read-only API server가 기존 frontend DTO contract를 유지하면서 live Postgres state를 HTTP로 제공한다.

## Why

- stdlib fixture server는 local/smoke 용도에는 충분하지만 production 후보로 키우기에는 OpenAPI, ASGI lifecycle, middleware, DB connection pooling 경계가 약하다.
- DB-backed HTTP smoke가 이미 통과했으므로 다음 병목은 framework와 connection boundary 결정이다.

## Scope

- 포함:
  - FastAPI app factory
  - Uvicorn console entrypoint
  - psycopg pool-backed executor
  - `STOCKANALYSIS_DATABASE_URL` runtime env
  - read-token auth seam
  - CORS/error boundary
  - Next server-side bearer token forwarding
  - unit/ASGI/Docker smoke verification
  - docs/task handoff 갱신
- 제외:
  - write endpoint
  - full auth/RBAC/session/actor identity
  - audit write model
  - broker/order flow
  - DB schema/scoring/benchmark/evaluation split 변경
  - production deployment manifests
  - broad observability stack

## Mutable Surface

- 수정 가능한 파일:
  - `pyproject.toml`
  - `src/stockanalysis/ingest/config.py`
  - `src/stockanalysis/frontend/runtime_policy.py`
  - `src/stockanalysis/frontend/db_pool.py`
  - `src/stockanalysis/frontend/api_server.py`
  - `apps/web/src/lib/frontend-api.ts`
  - `tests/test_frontend_api_server.py`
  - `tests/test_frontend_db_pool.py`
  - `scripts/verify_frontend_api_server.sh`
  - `docs/frontend-api-server.md`
  - `docs/frontend-api-runtime-boundary.md`
  - `docs/frontend-architecture.md`
  - `docs/project-execution-roadmap.md`
  - `docs/verification-plan.md`
  - `README.md`
  - `AGENTS.md`
  - `scripts/verify_project_execution_roadmap.sh`
  - `docs/plans/2026-05-03-frontend-api-server-framework-decision.md`
  - `docs/tasks/frontend-api-server-framework-decision/`
- 수정 금지 파일:
  - DB migrations
  - scoring formula
  - benchmark/evaluation split
  - secrets/env files
  - broker/order implementation

## Verification Commands

- 검증에 사용할 명령:
  - `python3 -m py_compile src/stockanalysis/frontend/api_server.py src/stockanalysis/frontend/db_pool.py src/stockanalysis/frontend/runtime_policy.py src/stockanalysis/ingest/config.py`
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_server tests.test_frontend_db_pool -v`
  - `bash scripts/verify_frontend_api_server.sh`
  - `bash scripts/verify_frontend_api_runtime_boundary.sh`
  - `bash scripts/verify_frontend_runtime_db_smoke.sh`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `cd apps/web && npm run typecheck`
  - `PYTHONPATH=src python3 -m unittest discover -s tests`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-server-framework-decision`
  - `rg -n "\[[A-Z_]+\]" AGENTS.md docs -S`
  - `git diff --check`

## Deliverables

- FastAPI read-only API server
- psycopg pool executor
- Next server-side token forwarding
- Docker-backed FastAPI live smoke
- docs/task handoff/review

## Completion Criteria

- [x] FastAPI server serves `/__health`, `/__endpoints`, and live `/api/...` DTOs.
- [x] Production profile uses read-token auth and explicit CORS.
- [x] `STOCKANALYSIS_DATABASE_URL` is supported without exposing it in metadata.
- [x] Existing stdlib fixture server remains available.
- [x] Write methods remain blocked.
- [x] Verification commands pass and evidence is recorded.

## Risks

- This slice still does not implement full identity/RBAC.
- Uvicorn deployment topology, structured request logs, request id, and alerting are deferred.
