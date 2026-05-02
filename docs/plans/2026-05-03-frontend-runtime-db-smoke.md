# Frontend Runtime DB Smoke Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prove the read-only frontend HTTP runtime can serve live DTOs from an actual Postgres database through `STOCKANALYSIS_PSQL_COMMAND`.

**Architecture:** Reuse the existing stdlib HTTP runtime and live adapter. The verification script starts a disposable Postgres container, applies migrations/seeds, runs the deterministic fixture pipeline, starts the runtime in guarded live mode, and fetches representative endpoints over HTTP with bearer-token auth.

**Tech Stack:** Bash, Docker Postgres, Python stdlib HTTP server, `urllib`, existing `stockanalysis.ingest.cli`, existing frontend live adapter.

---

### Task 1: Lock Harness Scope

**Files:**
- Create: `docs/tasks/frontend-runtime-db-smoke/contract.md`
- Create: `docs/tasks/frontend-runtime-db-smoke/plan.md`
- Create: `docs/tasks/frontend-runtime-db-smoke/handoff.md`
- Create: `docs/tasks/frontend-runtime-db-smoke/review.md`

**Steps:**
1. Record in-scope and out-of-scope boundaries.
2. State that schema, benchmark, scoring, write APIs, auth/RBAC, and connection pooling are not changed.
3. List exact verification commands.

### Task 2: Add DB-Backed HTTP Smoke Script

**Files:**
- Create: `scripts/verify_frontend_runtime_db_smoke.sh`

**Steps:**
1. Start a disposable Postgres container.
2. Apply all migrations and seeds.
3. Run the deterministic fixture pipeline through portfolio remediation daily automation.
4. Start `create_frontend_fixture_server` with `source="live"`, `runtime_profile="production"`, explicit CORS, and `auth_mode="read-token"`.
5. Fetch `/__health` publicly.
6. Assert an unauthenticated `/api/dashboard/today` request returns `401`.
7. Fetch live endpoints with `Authorization: Bearer <token>` and assert DTO fields from database state.

### Task 3: Wire Verification Docs

**Files:**
- Create: `docs/frontend-runtime-db-smoke.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/frontend-api-runtime-boundary.md`
- Modify: `docs/frontend-architecture.md`

**Steps:**
1. Document the new runtime smoke command and what it proves.
2. Update immediate next task references away from completed live-read slices.
3. Keep later work as connection pooling, server framework, auth/RBAC, and deployment.

### Task 4: Verify and Review

**Files:**
- Modify: `docs/tasks/frontend-runtime-db-smoke/handoff.md`
- Modify: `docs/tasks/frontend-runtime-db-smoke/review.md`

**Steps:**
1. Run `bash scripts/verify_frontend_runtime_db_smoke.sh`.
2. Run `bash scripts/verify_project_execution_roadmap.sh`.
3. Run `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-runtime-db-smoke`.
4. Run `PYTHONPATH=src python3 -m unittest discover -s tests`.
5. Run placeholder and diff checks.
