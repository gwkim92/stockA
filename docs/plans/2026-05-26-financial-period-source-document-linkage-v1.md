# financial-period-source-document-linkage-v1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Connect SEC filing source documents and raw filing artifacts to canonical financial statement periods so reported segment parsing can run on real filings.

**Architecture:** Add a backend operation under `stockanalysis-operations` that coordinates existing SEC filings/companyfacts/raw-fetch services and a deterministic SQL backfill. The operation is bounded, preview-first, and does not touch recommendation scores, weights, benchmarks, or broker/order flow.

**Tech Stack:** Python operations CLI, Postgres SQL, existing SEC ingest services, existing `ops.pipeline_run` provenance.

---

### Task 1: Contract And SQL Preview

**Files:**
- Create: `docs/tasks/financial-period-source-document-linkage-v1/contract.md`
- Create: `src/stockanalysis/operations/financial_period_source_linkage.py`
- Test: `tests/test_financial_period_source_linkage.py`

**Steps:**
1. Write tests for read-only preview SQL.
2. Implement `render_financial_period_source_linkage_preview_sql`.
3. Verify preview reports period/source/raw coverage.

### Task 2: Backfill And Raw Candidate SQL

**Files:**
- Modify: `src/stockanalysis/operations/financial_period_source_linkage.py`
- Test: `tests/test_financial_period_source_linkage.py`

**Steps:**
1. Write tests for backfill SQL and raw fetch candidate SQL.
2. Implement matching by instrument/company text, statement scope, and filing/report date.
3. Ensure backfill is bounded to null `source_document_id` periods and returns JSON summary.

### Task 3: Runner And CLI

**Files:**
- Modify: `src/stockanalysis/operations/financial_period_source_linkage.py`
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_financial_period_source_linkage.py`
- Test: `tests/test_data_operations_cli.py`

**Steps:**
1. Add `run_financial_period_source_linkage`.
2. In execute mode, create an operation run, call SEC filings/companyfacts refresh when CIK is supplied, backfill links, then raw-fetch a bounded number of linked docs.
3. Add `financial-period-source-linkage-run` CLI.
4. Keep `recommendation_scoring_mutated=false`.

### Task 4: Cadence/Profile Integration

**Files:**
- Modify: `src/stockanalysis/operations/cadence.py`
- Modify: `src/stockanalysis/operations/operating_data_orchestrator.py`
- Test: `tests/test_data_operations_cadence.py`
- Test: `tests/test_operating_data_orchestrator.py`

**Steps:**
1. Add weekly cadence row.
2. Insert profile step before `reported-segment-footnote-parser`.
3. Verify generated commands are secret-free and ordered correctly.

### Task 5: Verification And Handoff

**Files:**
- Create: `docs/tasks/financial-period-source-document-linkage-v1/handoff.md`
- Create: `docs/tasks/financial-period-source-document-linkage-v1/review.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Steps:**
1. Run contract tests and compileall.
2. Run roadmap and AWH verification.
3. Run EC2 smoke and record whether parser candidates are unblocked.
