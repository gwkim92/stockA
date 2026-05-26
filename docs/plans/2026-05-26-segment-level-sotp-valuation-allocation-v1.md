# Segment-Level SOTP Valuation Allocation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Derive and display segment-level SOTP valuation allocation evidence from SEC-reported segment revenue and operating income without changing recommendation weights or order boundaries.

**Architecture:** Keep the canonical SOTP component table unchanged. Add allocation JSON inside existing SOTP assumptions by splitting the current operating-business component value across reported segments using deterministic revenue/operating-income shares, then expose that JSON through the existing live adapter and valuation card.

**Tech Stack:** Python SQL renderer, Postgres JSONB assumptions, FastAPI live adapter DTOs, Next.js/TypeScript valuation card, unittest, AWH verification.

---

### Task 1: Contract And Baseline

**Files:**
- Create: `docs/tasks/segment-level-sotp-valuation-allocation-v1/contract.md`
- Create: `docs/tasks/segment-level-sotp-valuation-allocation-v1/handoff.md`
- Create: `docs/tasks/segment-level-sotp-valuation-allocation-v1/review.md`
- Create: `docs/plans/2026-05-26-segment-level-sotp-valuation-allocation-v1.md`

**Steps:**
1. Record mutable surface, non-goals, verification commands, and acceptance criteria.
2. Keep recommendation weight and order boundary exclusions explicit.

### Task 2: SOTP SQL Allocation Evidence

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Test: `tests/test_professional_equity_analysis.py`

**Steps:**
1. Add failing assertions that SOTP SQL emits `reported_segment_allocations`, allocation basis, allocated fair values, and no score component mutation.
2. Extend the SOTP SQL with segment allocation rows.
3. Allocate existing operating-business low/base/high fair values across segments using operating income share first, revenue share fallback.
4. Store allocations in operating-business component assumptions and valuation snapshot assumptions.
5. Run focused Python tests.

### Task 3: API DTO And Frontend

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/components/valuation-target-range-card.tsx`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
1. Add DTO assertions for `reported_segment_allocations`.
2. Normalize allocation payload from valuation assumptions or component assumptions.
3. Extend TypeScript types.
4. Render Korean allocation rows under SOTP.
5. Run frontend typecheck and focused tests.

### Task 4: Verification And EC2 Smoke

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/segment-level-sotp-valuation-allocation-v1/handoff.md`
- Modify: `docs/tasks/segment-level-sotp-valuation-allocation-v1/review.md`

**Steps:**
1. Run local focused tests, regression tests, typecheck, compileall, roadmap verifier, AWH verifier, and full Python 3.13 suite.
2. Commit and push.
3. Deploy to EC2 with fast-forward.
4. Rerun SOTP and valuation snapshot.
5. Verify `/api/stocks/AAPL` and `/stocks/AAPL` expose segment allocations with read-only boundaries.
