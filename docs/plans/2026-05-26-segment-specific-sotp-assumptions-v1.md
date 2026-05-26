# Segment Specific SOTP Assumptions Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add evidence-only segment-specific growth, margin, multiple, and driver assumptions to SOTP without changing SOTP totals, recommendation weights, or order boundaries.

**Architecture:** Keep schema unchanged. Use existing reported segment input and allocation rows to build deterministic assumptions in `market.sum_of_parts_component.assumptions_json`, propagate them into valuation snapshot assumptions, expose them through the live adapter, and render them in Korean.

**Tech Stack:** Python SQL renderer, Postgres JSON assumptions, FastAPI live adapter DTO, Next.js TypeScript UI, unittest, AWH verification.

---

### Task 1: Contract And Baseline

**Files:**
- Create: `docs/tasks/segment-specific-sotp-assumptions-v1/contract.md`
- Create: `docs/tasks/segment-specific-sotp-assumptions-v1/handoff.md`
- Create: `docs/tasks/segment-specific-sotp-assumptions-v1/review.md`
- Create: `docs/plans/2026-05-26-segment-specific-sotp-assumptions-v1.md`

**Steps:**
1. Record mutable surface, non-goals, verification commands, and acceptance criteria.
2. Preserve score/order/benchmark boundaries.

### Task 2: Backend SOTP Assumptions

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Test: `tests/test_professional_equity_analysis.py`

**Steps:**
1. Add CTE for segment-level assumption rows using reported segment inputs and allocation rows.
2. Store `reported_segment_assumptions` in operating-business component assumptions and SOTP valuation snapshot assumptions.
3. Update limitations from “not modeled” to “proxy assumptions, not yet segment DCF.”
4. Run focused Python tests.

### Task 3: Live DTO And Frontend

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/components/valuation-target-range-card.tsx`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
1. Normalize `reported_segment_assumptions` into live DTO shape.
2. Add TypeScript contract fields.
3. Render `사업부별 가정` section in Korean.
4. Run focused tests and frontend typecheck.

### Task 4: Verification And Handoff

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/segment-specific-sotp-assumptions-v1/handoff.md`
- Modify: `docs/tasks/segment-specific-sotp-assumptions-v1/review.md`

**Steps:**
1. Run focused tests, regression slice, frontend typecheck, compileall, roadmap verifier, AWH verifier, and diff check.
2. Commit and push.
3. Deploy to EC2 with fast-forward.
4. Rerun SOTP and valuation snapshot.
5. Verify `/api/stocks/AAPL` exposes segment assumptions and `/stocks/AAPL` renders Korean assumption rows.
