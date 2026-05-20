# Local Ingest Worker Data Health Visibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Show the latest local ingest worker run status in `/api/data-health` and `/data-health` separately from manual smoke and scheduler activation.

**Architecture:** Reuse the repo-outside worker report produced by `stockanalysis-operations local-ingest-worker-run --output`. Add a sanitized read model to the operations module, expose it as an additive frontend API DTO field, and render it in the existing Next.js Server Component page without adding client state.

**Tech Stack:** Python operations/read adapter, FastAPI read-only DTO boundary, Next.js Server Components, TypeScript types, unittest.

---

### Task 1: Record Guardrail

**Files:**
- Create: `docs/tasks/local-ingest-worker-data-health-visibility/contract.md`
- Modify: `AGENTS.md`
- Modify: `docs/project-execution-roadmap.md`

**Steps:**
- Record that this is visibility only, not scheduler activation.
- Keep `launchctl`, LaunchAgents writes, external scheduler deployment, DB schema, scoring, paid LLM, and broker/order flow out of scope.

### Task 2: Add Sanitized Worker Visibility Loader

**Files:**
- Modify: `src/stockanalysis/operations/local_ingest_worker.py`
- Test: `tests/test_local_ingest_worker.py`

**Steps:**
- Add `STOCKANALYSIS_LOCAL_INGEST_WORKER_REPORT`.
- Add `load_local_ingest_worker_visibility_report`.
- Return `not_configured`, `missing_report`, `invalid_report`, or sanitized worker status.
- Never expose env file values, database URLs, tokens, or raw command values.

### Task 3: Expose DTO and UI

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `tests/test_frontend_live_adapter.py`
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/app/data-health/page.tsx`
- Modify: `docs/api/frontend/examples/data-health.json`
- Modify: `docs/frontend-api-contract.md`

**Steps:**
- Add additive `local_ingest_worker` field to `/api/data-health`.
- Add a Korean worker card that explains local process worker status separately from manual smoke and scheduler activation.
- Keep the page as an async Server Component.

### Task 4: Verify and Handoff

**Files:**
- Create: `scripts/verify_local_ingest_worker_data_health_visibility.sh`
- Create: `docs/local-ingest-worker-data-health-visibility.md`
- Create: `docs/tasks/local-ingest-worker-data-health-visibility/handoff.md`
- Create: `docs/tasks/local-ingest-worker-data-health-visibility/review.md`
- Modify: `docs/verification-plan.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Steps:**
- Run focused Python tests.
- Run Next typecheck.
- Run roadmap verification, AWH task verification, and diff whitespace check.
