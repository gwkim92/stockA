# Reported Segment Unit Normalization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Infer SEC reported segment metric units from table-neighborhood context and render Korean unit labels without changing valuation totals or recommendation behavior.

**Architecture:** Keep storage schema unchanged. Extend the deterministic parser so unit inference receives both the table HTML and nearby filing prose, then flow the existing `metric_unit` field through SOTP evidence and frontend labels.

**Tech Stack:** Python HTML parsing helpers, Postgres existing JSON/metric fields, Next.js TypeScript UI, unittest, AWH verification.

---

### Task 1: Contract And Baseline

**Files:**
- Create: `docs/tasks/reported-segment-unit-normalization-v1/contract.md`
- Create: `docs/tasks/reported-segment-unit-normalization-v1/handoff.md`
- Create: `docs/tasks/reported-segment-unit-normalization-v1/review.md`
- Create: `docs/plans/2026-05-26-reported-segment-unit-normalization-v1.md`

**Steps:**
1. Record mutable surface, non-goals, verification commands, and acceptance criteria.
2. Explicitly preserve score/order/benchmark boundaries.

### Task 2: Parser Unit Context

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Test: `tests/test_professional_equity_analysis.py`

**Steps:**
1. Add failing assertion that Apple transposed fixture rows all use `USD_millions_as_reported`.
2. Add helper that returns each table with nearby context text.
3. Pass table context into `_infer_segment_metric_unit`.
4. Add unit metadata to row assumptions.
5. Run focused Python tests.

### Task 3: Frontend Unit Labels

**Files:**
- Modify: `apps/web/src/components/valuation-target-range-card.tsx`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
1. Update fixture payload units to `USD_millions_as_reported`.
2. Render `백만 달러 단위` and `천 달러 단위` labels.
3. Run focused tests and `npm run typecheck`.

### Task 4: Verification And EC2 Smoke

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/reported-segment-unit-normalization-v1/handoff.md`
- Modify: `docs/tasks/reported-segment-unit-normalization-v1/review.md`

**Steps:**
1. Run local focused tests, regression tests, typecheck, compileall, roadmap verifier, AWH verifier, and full Python 3.13 suite.
2. Commit and push.
3. Deploy to EC2 with fast-forward.
4. Rerun reported segment parser, SOTP, and valuation snapshot.
5. Verify `/api/stocks/AAPL` and `/stocks/AAPL` show normalized unit labels with read-only boundaries.
