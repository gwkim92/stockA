# Segment SOTP Driver Calibration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade segment-specific SOTP assumptions from one-period margin/share proxies to transparent trend/template-calibrated evidence without changing scores, SOTP totals, or order boundaries.

**Architecture:** Reuse existing `research.segment_footnote_evidence`, `market.sum_of_parts_component.assumptions_json`, and `market.valuation_snapshot.assumptions_json`. Add SQL CTEs for historical segment periods, compute trend fields, attach deterministic driver templates, expose via the live DTO, and render Korean context.

**Tech Stack:** Python SQL renderer, Postgres JSON assumptions, FastAPI live adapter DTO, Next.js TypeScript UI, unittest, AWH verification.

---

### Task 1: Contract And Baseline

**Files:**
- Create: `docs/tasks/segment-sotp-driver-calibration-v1/contract.md`
- Create: `docs/tasks/segment-sotp-driver-calibration-v1/handoff.md`
- Create: `docs/tasks/segment-sotp-driver-calibration-v1/review.md`
- Create: `docs/plans/2026-05-26-segment-sotp-driver-calibration-v1.md`

**Steps:**
1. Record mutable surface, non-goals, verification commands, and acceptance criteria.
2. Preserve score/order/benchmark boundaries.

### Task 2: Backend Trend Calibration

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Test: `tests/test_professional_equity_analysis.py`

**Steps:**
1. Add historical segment rows, ranked anchors, and trend CTEs.
2. Add driver template key/label.
3. Add calibration fields to `reported_segment_assumptions`.
4. Keep SOTP totals unchanged.

### Task 3: DTO And Frontend

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/components/valuation-target-range-card.tsx`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
1. Expose calibration fields in SOTP evidence.
2. Add TypeScript fields.
3. Render Korean trend/proxy context below segment assumptions.

### Task 4: Verification And EC2 Smoke

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/segment-sotp-driver-calibration-v1/handoff.md`
- Modify: `docs/tasks/segment-sotp-driver-calibration-v1/review.md`

**Steps:**
1. Run focused tests, regression slice, frontend typecheck, compileall, roadmap verifier, AWH verifier, diff check, and full Python suite if needed.
2. Commit and push.
3. Deploy to EC2 with fast-forward.
4. Rerun SOTP and valuation snapshot.
5. Verify `/api/stocks/AAPL` and `/stocks/AAPL` expose calibration evidence.
