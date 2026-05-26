# reported-segment-parser-quality-v1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Expand the deterministic reported segment parser so real Apple-style transposed SEC segment tables produce `reported_segment_metric` evidence.

**Architecture:** Keep the existing backend runner and evidence table unchanged. Add a second parsing path inside `extract_reported_segment_metrics_from_html` for tables where segment labels are column headers and supported metrics are row labels. Preserve existing simple table parsing and all read-only scoring/order guardrails.

**Tech Stack:** Python stdlib HTML/regex parser, existing `stockanalysis-operations` runner, Postgres evidence upsert, unittest.

---

### Task 1: Root Cause Fixture

**Files:**
- Create: `tests/fixtures/sec_filing_aapl_transposed_segment_sample.html`
- Modify: `tests/test_professional_equity_analysis.py`

**Steps:**
1. Add a minimal fixture matching Apple 10-K reportable segment table shape.
2. Add a failing unit test expecting 10 rows: 5 reportable segments times 2 metrics.
3. Assert `Corporate` and `Total` are excluded.

### Task 2: Parser Expansion

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`

**Steps:**
1. Add helper logic to detect a transposed segment table with a year row and segment header row.
2. Add value alignment that ignores standalone currency marker cells.
3. Map `Net sales` to `segment_revenue` and `Operating income/(loss)` to `segment_operating_income`.
4. Append evidence rows using the same provenance and confidence structure as existing parser rows.

### Task 3: Verification And Handoff

**Files:**
- Create: `docs/tasks/reported-segment-parser-quality-v1/handoff.md`
- Create: `docs/tasks/reported-segment-parser-quality-v1/review.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Steps:**
1. Run focused parser tests and professional analysis regression.
2. Run compileall, roadmap verify, and AWH verify.
3. Commit and push.
4. Deploy to EC2 and rerun `reported-segment-footnote-parser-run --execute`.
5. Record whether Apple 10-K now produces reported segment metrics.
