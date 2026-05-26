# Sum Of The Parts Valuation Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a conservative sum-of-the-parts valuation evidence layer that separates operating value, balance-sheet adjustment, and data-gap reserve without changing recommendation weights or order flow.

**Architecture:** Add canonical SOTP component rows in Postgres, then aggregate them into `market.valuation_snapshot.method='sum_of_parts'`. Frontend reads the existing valuation target range DTO plus a new SOTP evidence payload and renders it in the shared valuation card.

**Tech Stack:** Python stdlib SQL renderers, Postgres migrations, FastAPI read adapter DTOs, Next.js/React valuation card, unittest, AWH task verification.

---

### Task 1: Schema And Runner Contract

**Files:**
- Create: `db/migrations/0025_sum_of_parts_valuation.sql`
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Test: `tests/test_professional_equity_analysis.py`

**Steps:**
1. Add migration for `market.sum_of_parts_component` and alter `market.valuation_snapshot.method` check to allow `sum_of_parts`.
2. Add constants for SOTP pipeline/model/component types.
3. Add `render_sum_of_parts_valuation_preview_sql`.
4. Add `render_sum_of_parts_valuation_upsert_sql`.
5. Add `load_sum_of_parts_valuation_preview` and `run_sum_of_parts_valuation`.
6. Add tests for migration, preview read-only behavior, upsert SQL, dry-run, and execute.

### Task 2: CLI And Operations Integration

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Modify: `src/stockanalysis/operations/cadence.py`
- Modify: `src/stockanalysis/operations/operating_data_orchestrator.py`
- Modify: `src/stockanalysis/operations/professional_coverage_expansion.py`
- Test: `tests/test_data_operations_cli.py`
- Test: `tests/test_data_operations_cadence.py`
- Test: `tests/test_operating_data_orchestrator.py`
- Test: `tests/test_professional_coverage_expansion.py`

**Steps:**
1. Add `sum-of-parts-valuation-run` CLI.
2. Add weekly cadence job after forecast inputs and before valuation snapshot.
3. Add operating-data profile step in the same order.
4. Add professional coverage expansion downstream call before valuation snapshot.
5. Update tests to prove ordering and command wiring.

### Task 3: Valuation Snapshot Aggregation

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Test: `tests/test_professional_equity_analysis.py`

**Steps:**
1. Extend `VALUATION_METHODS` with `sum_of_parts`.
2. Extend valuation preview to report SOTP component coverage.
3. Extend valuation upsert SQL to aggregate latest SOTP components into `sum_of_parts` valuation rows.
4. Store SOTP components, component count, source, data quality, and limitations in `assumptions_json`.
5. Verify `recommendation_scoring_mutated=false` remains present.

### Task 4: Frontend DTO And Shared Card

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/components/valuation-target-range-card.tsx`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
1. Add SOTP label, evidence summary, assumption items, sensitivity text, expected data keys, and limitations.
2. Add `sotp_evidence` payload from valuation assumptions.
3. Add TypeScript type fields for SOTP component evidence.
4. Render SOTP component rows in the valuation card when available.
5. Update frontend adapter tests to assert SOTP evidence is present.

### Task 5: Verification, Docs, And Deployment Evidence

**Files:**
- Modify: `docs/tasks/sum-of-the-parts-valuation-foundation-v1/handoff.md`
- Modify: `docs/tasks/sum-of-the-parts-valuation-foundation-v1/review.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Steps:**
1. Run targeted Python tests.
2. Run compileall, full unittest, Next typecheck/build, migration verifier, roadmap verifier, and AWH verify.
3. Commit and push.
4. Deploy to EC2, apply migration, run SOTP and valuation snapshot runners, and smoke API/routes.
5. Record EC2 evidence in handoff/review/roadmap/AGENTS.
