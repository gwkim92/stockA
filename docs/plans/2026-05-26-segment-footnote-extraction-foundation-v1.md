# Segment Footnote Extraction Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a canonical SEC segment/footnote evidence foundation and surface it inside SOTP valuation evidence without changing recommendation scores.

**Architecture:** Store deterministic SEC filing anchors, consolidated metric evidence, and explicit segment data gaps in `research.segment_footnote_evidence`. The operations runner writes evidence rows through the existing `stockanalysis-operations` backend CLI, and valuation snapshots consume the evidence as assumptions only.

**Tech Stack:** Python stdlib, Postgres SQL migrations, existing `PsqlCommandExecutor`, FastAPI DTO live adapter, Next.js/React valuation card.

---

### Task 1: Schema And Contract

**Files:**
- Create: `db/migrations/0026_segment_footnote_evidence.sql`
- Create: `docs/tasks/segment-footnote-extraction-foundation-v1/contract.md`
- Create: `docs/plans/2026-05-26-segment-footnote-extraction-foundation-v1.md`
- Test: `tests/test_professional_equity_analysis.py`

**Steps:**
- Add `research.segment_footnote_evidence`.
- Add lookup indexes for instrument/date/scope and source document.
- Add a migration unit assertion.

### Task 2: Runner And CLI

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_professional_equity_analysis.py`
- Test: `tests/test_data_operations_cli.py`

**Steps:**
- Add preview SQL.
- Add execute/upsert SQL.
- Add `run_segment_footnote_evidence`.
- Add `segment-footnote-evidence-run` CLI.
- Verify dry-run and execute guardrails.

### Task 3: Operations Integration

**Files:**
- Modify: `src/stockanalysis/operations/cadence.py`
- Modify: `src/stockanalysis/operations/operating_data_orchestrator.py`
- Modify: `src/stockanalysis/operations/professional_coverage_expansion.py`
- Test: `tests/test_data_operations_cadence.py`
- Test: `tests/test_operating_data_orchestrator.py`
- Test: `tests/test_professional_coverage_expansion.py`

**Steps:**
- Add weekly cadence after financial forecast inputs and before SOTP valuation.
- Add operating profile step.
- Add professional coverage downstream step.

### Task 4: SOTP Evidence And Frontend

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/components/valuation-target-range-card.tsx`
- Test: `tests/test_professional_equity_analysis.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Include segment evidence metadata in SOTP valuation assumptions.
- Normalize evidence in the frontend DTO.
- Render Korean segment/footnote evidence in the valuation card.

### Task 5: Verification And Handoff

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/segment-footnote-extraction-foundation-v1/handoff.md`
- Modify: `docs/tasks/segment-footnote-extraction-foundation-v1/review.md`

**Steps:**
- Run targeted Python tests.
- Run compileall, Next typecheck/build, migration verification, roadmap verification, and AWH task verify.
- If feasible, deploy/smoke on EC2.
- Update handoff with exact evidence.
