# Frontend API Server Observability Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** FastAPI read-only frontend API server에 request id, request timeout, structured access log, liveness/readiness probes를 추가한다.

**Architecture:** 기존 DTO contract와 live adapter는 유지하고, FastAPI route/middleware layer에서만 운영 경계를 강화한다. DB schema, scoring, benchmark, write API, auth/RBAC는 바꾸지 않는다.

**Tech Stack:** FastAPI, Starlette middleware, psycopg pool, Python unittest/TestClient, Docker Postgres smoke.

---

### Task 1: Lock Task Contract

**Files:**
- Create: `docs/tasks/frontend-api-server-observability-hardening/contract.md`
- Create: `docs/tasks/frontend-api-server-observability-hardening/plan.md`
- Create: `docs/tasks/frontend-api-server-observability-hardening/handoff.md`
- Create: `docs/tasks/frontend-api-server-observability-hardening/review.md`

**Steps:**
1. Define scope as read-only API server observability and readiness hardening.
2. Exclude write endpoints, full auth/RBAC, deployment manifests, schema/scoring/benchmark changes.
3. List verification commands before code is considered complete.

### Task 2: Add Runtime Observability Controls

**Files:**
- Modify: `src/stockanalysis/frontend/api_server.py`
- Test: `tests/test_frontend_api_server.py`

**Steps:**
1. Add deterministic request id generation and `X-Request-ID` propagation.
2. Add structured JSON access logs with method, path, status, duration, source mode, profile, and request id.
3. Add configurable request timeout and stable timeout error envelope.
4. Verify local tests cover generated and inbound request ids, logging, and timeout response.

### Task 3: Add Probe Routes

**Files:**
- Modify: `src/stockanalysis/frontend/api_server.py`
- Test: `tests/test_frontend_api_server.py`

**Steps:**
1. Add public `/__live` route that only proves process liveness.
2. Add public `/__ready` route that proves contract load and live DB readiness when psycopg pool is active.
3. Ensure readiness does not expose DB URL, SQL, token, or credential details.
4. Verify healthy and not-ready states with TestClient/fake app state.

### Task 4: Extend Smoke Verification

**Files:**
- Modify: `scripts/verify_frontend_api_server.sh`

**Steps:**
1. Check `/__live` and `/__ready` during Docker-backed FastAPI smoke.
2. Check `X-Request-ID` echo behavior.
3. Check timeout/auth boundaries without adding write APIs.

### Task 5: Update Docs And Roadmap

**Files:**
- Modify: `docs/frontend-api-server.md`
- Modify: `docs/frontend-api-runtime-boundary.md`
- Modify: `docs/frontend-architecture.md`
- Modify: `docs/frontend-runtime-db-smoke.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/frontend-api-server-observability-hardening/handoff.md`
- Modify: `docs/tasks/frontend-api-server-observability-hardening/review.md`

**Steps:**
1. Document new probes and operational headers.
2. Move immediate next task to the next API runtime gap after hardening.
3. Record verification evidence and remaining risks.

### Task 6: Verify And Publish

**Commands:**
- `PYTHONPATH=src python3 -m unittest tests.test_frontend_api_server -v`
- `bash scripts/verify_frontend_api_server.sh`
- `bash scripts/verify_frontend_api_runtime_boundary.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-server-observability-hardening`
- `git diff --check`

**Steps:**
1. Run targeted tests first.
2. Run Docker smoke after targeted tests pass.
3. Run project roadmap and AWH verification.
4. Commit, push, and open PR.
