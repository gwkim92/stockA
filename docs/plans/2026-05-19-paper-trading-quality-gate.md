# Paper Trading Quality Gate Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a read-only paper trading preview and recommendation quality gate so the operator can see recommendation/position conflicts before any trade automation exists.

**Architecture:** Keep the live FastAPI server read-only. Add a denormalized frontend DTO sourced from existing recommendation, position, price, and performance outcome tables. The page shows simulated paper actions only; it creates no orders, broker calls, or ledger writes.

**Tech Stack:** Python live adapter SQL, FastAPI existing route bridge, Next.js app router, existing contract fixture server, unittest.

---

### Task 1: Harness Scope

**Files:**
- Create: `docs/tasks/paper-trading-quality-gate/contract.md`
- Create: `docs/tasks/paper-trading-quality-gate/handoff.md`

**Steps:**
- Record that this slice is read-only paper trading preview, not real trading or order write.
- Define mutable surface and verification commands.

### Task 2: Frontend API Contract

**Files:**
- Modify: `docs/api/frontend/contract-index.json`
- Create: `docs/api/frontend/examples/paper-trading-preview.json`
- Modify: `docs/frontend-api-contract.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`

**Steps:**
- Add `GET /api/paper-trading/preview`.
- Keep response shape under `frontend-api-v0.1`.
- Include summary metrics, paper action rows, and explicit read-only guardrails.

### Task 3: Live Adapter

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `src/stockanalysis/frontend/pagination.py`
- Test: `tests/test_frontend_live_adapter.py`
- Test: `tests/test_frontend_api_adapter.py`
- Test: `tests/test_frontend_fixture_server.py`

**Steps:**
- Add SQL renderer for latest recommendation batch, latest portfolio snapshot, latest prices, and measured recommendation outcomes.
- Build DTO payload with `paper_action`, current/target weights, human approval requirement, and quality summary.
- Add pagination support for `paper_actions`.

### Task 4: Next.js Page

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/frontend-api.ts`
- Create: `apps/web/src/app/paper-trading/page.tsx`
- Modify: `apps/web/src/app/layout.tsx`
- Modify: `apps/web/src/app/page.tsx`
- Modify: `apps/web/src/lib/korean-labels.ts`

**Steps:**
- Add a “Paper 거래” page that explains no real orders are placed.
- Show quality summary, paper action list, and guardrails in Korean operator wording.

### Task 5: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_api_adapter tests.test_frontend_live_adapter tests.test_frontend_fixture_server`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- live HTTP smoke for `/api/paper-trading/preview` and `/paper-trading`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task paper-trading-quality-gate`
- `git diff --check`
