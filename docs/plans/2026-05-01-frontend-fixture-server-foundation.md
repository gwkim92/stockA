# Frontend Fixture Server Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expose the frontend API fixture adapter through a local read-only HTTP server so the future web app can fetch contract-shaped payloads.

**Architecture:** The server wraps `stockanalysis.frontend.api_adapter` and keeps `docs/api/frontend/contract-index.json` as the source of truth. It uses Python standard library HTTP primitives to avoid adding production API framework decisions before the live DB read adapter exists.

**Tech Stack:** Python 3.11+, `http.server`, `urllib`, `unittest`, bash verification scripts.

---

### Task 1: Task Boundary

**Files:**
- Create: `docs/tasks/frontend-fixture-server-foundation/contract.md`
- Create: `docs/tasks/frontend-fixture-server-foundation/plan.md`
- Create: `docs/tasks/frontend-fixture-server-foundation/handoff.md`
- Create: `docs/tasks/frontend-fixture-server-foundation/review.md`

**Step 1: Define scope**

Document that this task includes a local read-only fixture HTTP server, tests, verification script, and docs.

**Step 2: Define exclusions**

Document that this task excludes live DB reads, auth, frontend scaffold, deployment config, and write endpoints.

**Step 3: Define verification**

List syntax, unit, server smoke, frontend API contract, adapter verification, AWH task verification, and placeholder checks.

### Task 2: Server Module

**Files:**
- Create: `src/stockanalysis/frontend/fixture_server.py`
- Modify: `pyproject.toml`

**Step 1: Write server module**

Implement a `ThreadingHTTPServer` handler that supports:

- `GET /__health`
- `GET /__endpoints`
- exact `GET` fixture paths from the contract index
- stable JSON 404 for unknown API paths
- stable JSON 405 for non-read methods
- CORS headers for local frontend development

**Step 2: Add CLI entrypoint**

Expose `stockanalysis-frontend-fixture-server = "stockanalysis.frontend.fixture_server:main_entry"`.

### Task 3: Tests

**Files:**
- Create: `tests/test_frontend_fixture_server.py`

**Step 1: Add server lifecycle fixture**

Start the fixture server on `127.0.0.1:0` in a background thread and shut it down after tests.

**Step 2: Verify healthy reads**

Assert `/__health`, `/__endpoints`, `/api/dashboard/today`, and a query-string endpoint return valid JSON.

**Step 3: Verify stable failure paths**

Assert unknown GET paths return 404 with `FrontendApiPathNotFound`, and POST returns 405 with `MethodNotAllowed`.

### Task 4: Verification Script

**Files:**
- Create: `scripts/verify_frontend_fixture_server.sh`

**Step 1: Add syntax and unit checks**

Run script syntax, compileall, server tests, adapter verification, and frontend API contract verification.

**Step 2: Add runtime smoke**

Launch the fixture server on a temporary localhost port, fetch `/__health`, `/__endpoints`, `/api/dashboard/today`, and `/api/remediation-tickets?status=open`, then confirm expected JSON fields.

**Step 3: Guard boundaries**

Confirm `apps/web` and `app` still do not exist.

### Task 5: Documentation

**Files:**
- Create: `docs/frontend-fixture-server.md`
- Modify: `README.md`
- Modify: `docs/frontend-api-adapter.md`
- Modify: `docs/frontend-api-contract.md`
- Modify: `docs/frontend-architecture.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/frontend-fixture-server-foundation/handoff.md`
- Modify: `docs/tasks/frontend-fixture-server-foundation/review.md`

**Step 1: Document usage**

Document how to start the server and what endpoints exist.

**Step 2: Update project maps**

Add the server doc and verification command to README and verification plan.

**Step 3: Update phase status**

Mark fixture server as complete and keep `apps/web` as the next browser-facing implementation step.

### Task 6: Final Verification

**Files:**
- No new files.

**Step 1: Run task verification**

Run:

```bash
bash -n scripts/verify_frontend_fixture_server.sh
bash scripts/verify_frontend_fixture_server.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-fixture-server-foundation
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```

**Step 2: Record evidence**

Update handoff and review with exact verification outcomes and unresolved risks.
