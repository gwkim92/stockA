# Segment History Backfill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Backfill historical reported segment periods from prior SEC filings so segment SOTP driver calibration can use multi-period trend evidence.

**Architecture:** Keep `research.segment_footnote_evidence` as the canonical segment metric store. Extend the parser candidate SQL to select a bounded number of historical periods per instrument, then add a backend operation that orchestrates source linkage/raw fetch, parser execution, SOTP rerun, and valuation snapshot rerun.

**Tech Stack:** Python backend CLI, Postgres SQL renderers, SEC raw filing artifacts, unittest, AWH verification, EC2 smoke.

---

### Task 1: Parser Candidate History Mode

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Test: `tests/test_professional_equity_analysis.py`

**Steps:**
1. Add `periods_per_instrument` to `render_reported_segment_footnote_candidates_sql`, `load_reported_segment_footnote_candidates`, and `run_reported_segment_footnote_parser`.
2. Replace `distinct on (period.instrument_id)` with ranked candidates and `period_rank <= periods_per_instrument`.
3. Keep default `periods_per_instrument=1` for backward compatibility.
4. Include `periods_per_instrument` in dry-run/execute reports.

### Task 2: CLI And Weekly Automation

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Modify: `src/stockanalysis/operations/operating_data_orchestrator.py`
- Test: `tests/test_data_operations_cli.py`
- Test: `tests/test_operating_data_orchestrator.py`

**Steps:**
1. Add `--periods-per-instrument` to `reported-segment-footnote-parser-run`.
2. Add weekly SEC profile arguments so the parser uses a bounded historical mode.
3. Keep commands redaction-safe and repo-outside env handling unchanged.

### Task 3: Segment History Backfill Runner

**Files:**
- Create: `src/stockanalysis/operations/segment_history_backfill.py`
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_segment_history_backfill.py`

**Steps:**
1. Add `segment-history-backfill-run`.
2. Dry-run reports planned source linkage, parser, SOTP, and valuation steps.
3. Execute mode creates a parent pipeline run and calls existing runners with bounded limits.
4. Store `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, and `order_boundary=read_only_no_order` in the report.

### Task 4: Verification And Handoff

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/segment-history-backfill-v1/handoff.md`
- Modify: `docs/tasks/segment-history-backfill-v1/review.md`

**Steps:**
1. Run focused tests, CLI help check, roadmap verifier, AWH verifier, compileall, and diff check.
2. Commit and push.
3. Deploy to EC2 with fast-forward.
4. Run `segment-history-backfill-run --execute`, then rerun route/API smoke for AAPL.
5. Record whether AAPL now has multi-period segment trend evidence or a specific source/parser blocker.
