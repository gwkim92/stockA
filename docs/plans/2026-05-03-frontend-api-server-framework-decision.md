# Frontend API Server Framework Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert the production-candidate frontend API runtime to FastAPI while preserving the stdlib fixture server for local fixture and legacy smoke workflows.

**Architecture:** Add a FastAPI app factory, a psycopg pool-backed executor that satisfies the existing live adapter interface, and a Docker-backed smoke that proves DB-backed HTTP reads over the new server. Keep existing DTO contracts and live adapter SQL unchanged.

**Tech Stack:** FastAPI, Uvicorn, psycopg pool, Python unittest, Docker Postgres, Next.js server-side fetch adapter.

---

### Task 1: Harness Scope

**Files:**
- Create: `docs/tasks/frontend-api-server-framework-decision/contract.md`
- Create: `docs/tasks/frontend-api-server-framework-decision/plan.md`
- Create: `docs/tasks/frontend-api-server-framework-decision/handoff.md`
- Create: `docs/tasks/frontend-api-server-framework-decision/review.md`

**Steps:**
1. Record FastAPI as the chosen framework.
2. Record that schema, scoring, benchmark, write APIs, broker flow, and full RBAC are out of scope.
3. List verification commands.

### Task 2: Runtime And DB Boundary

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/stockanalysis/ingest/config.py`
- Modify: `src/stockanalysis/frontend/runtime_policy.py`
- Create: `src/stockanalysis/frontend/db_pool.py`

**Steps:**
1. Add FastAPI/Uvicorn/psycopg/httpx dependencies.
2. Add `STOCKANALYSIS_DATABASE_URL` to runtime config and policy validation.
3. Add `PsycopgPoolExecutor` with `execute_scalar(sql)` and `execute_non_query(sql)`.

### Task 3: FastAPI Server

**Files:**
- Create: `src/stockanalysis/frontend/api_server.py`
- Modify: `apps/web/src/lib/frontend-api.ts`
- Modify: `pyproject.toml`

**Steps:**
1. Create a `create_app()` FastAPI app factory.
2. Add public `/__health`.
3. Add protected `/__endpoints` and `/api/{path:path}`.
4. Add stable error envelope and production redaction.
5. Add read-only method guard.
6. Add server-side bearer token forwarding in Next fetch adapter.

### Task 4: Tests And Smoke

**Files:**
- Create: `tests/test_frontend_api_server.py`
- Create: `tests/test_frontend_db_pool.py`
- Create: `scripts/verify_frontend_api_server.sh`

**Steps:**
1. Test FastAPI auth, endpoint index, live DTO routing, unsupported path redaction, and write method 405.
2. Test psycopg pool executor scalar behavior.
3. Add Docker Postgres + Uvicorn smoke.

### Task 5: Docs And Verification

**Files:**
- Create: `docs/frontend-api-server.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: task handoff/review.

**Steps:**
1. Document FastAPI server command, env, boundaries, and verification.
2. Update roadmap next task after this slice.
3. Run all required verification commands and record evidence.
