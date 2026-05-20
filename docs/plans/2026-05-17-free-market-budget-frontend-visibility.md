# Free Market Budget Frontend Visibility Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Surface local free-tier market data provider budget status in `/api/data-health` and the Next.js `/data-health` cockpit page.

**Architecture:** Keep the ledger read-only and path-driven through `STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH`. The backend returns a sanitized summary only; the frontend renders the summary if present. No DB schema or write endpoints are introduced.

**Tech Stack:** Python stdlib JSON/pathlib/datetime, existing FastAPI live adapter DTO path, Next.js Server Component, TypeScript.

---

### Task 1: Ledger Status Reader

**Files:**
- Modify: `src/stockanalysis/operations/market_price_free_backfill.py`
- Modify: `tests/test_market_price_free_backfill.py`

**Steps:**

1. Add tests for `load_market_price_provider_budget_status`:
   - env/path missing returns `status=not_configured`.
   - missing ledger file returns `status=ledger_missing` without path exposure.
   - valid ledger returns provider, date, daily budget, used, remaining, and latest run summary.
2. Implement the reader using existing `load_budget_ledger`.
3. Ensure no absolute file path appears in the returned payload.

### Task 2: Data Health DTO

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `tests/test_frontend_live_adapter.py`

**Steps:**

1. Add `provider_budget` to `build_live_data_health_response`.
2. Use the state `as_of_date` as budget date if parseable.
3. Add tests for both default not-configured and configured ledger status.
4. Keep contract version stable as additive `frontend-api-v0.1`.

### Task 3: Frontend Rendering

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/app/data-health/page.tsx`

**Steps:**

1. Extend `DataHealthData` with `provider_budget`.
2. Add a data-health card that shows provider, status, used/remaining/daily budget, and latest runner status.
3. Render `not_configured` as an explicit setup gate, not a crash.

### Task 4: Runtime Smoke And Docs

**Files:**
- Modify: `/private/tmp/stockanalysis-runtime/frontend-api.env` outside repo if present.
- Modify: task handoff/review docs.
- Modify: `docs/local-live-mvp-runtime.md` and local-live handoff.

**Steps:**

1. Add `STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH` to local frontend API env.
2. Restart or run a direct API resolver smoke if the live server process has not picked up new code.
3. Run Python tests, Next typecheck/build, AWH, roadmap, and `git diff --check`.
