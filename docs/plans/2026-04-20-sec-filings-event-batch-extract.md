# SEC Filings Event Batch Extract Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first batch pipeline that discovers pending SEC raw filings and turns them into event rows using the existing single-document extractor.

**Architecture:** Reuse `sec-filings-event-extract` as the per-document worker and add a thin batch layer that either accepts explicit accession numbers or queries pending `source_document` rows with raw artifacts and no `source` event link. Keep the batch stateless: return summary JSON and let each document keep its own `sec_filings_event_extract` pipeline run.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: Add pending discovery SQL and batch runner

**Files:**
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/sql.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/event_extract.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_sec_event_extract.py`

**Step 1: Write the failing test**

Add tests for:
- pending SEC document id discovery
- batch success summary
- continue-on-error behavior

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: FAIL with missing pending lookup or batch runner.

**Step 3: Write minimal implementation**

Add:
- SQL query for pending SEC document ids
- batch runner that reuses `run_sec_filings_event_extract`
- success/failure aggregation

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: all SEC event extraction tests pass.

**Step 5: Commit**

```bash
git add src/stockanalysis/ingest/sec/sql.py src/stockanalysis/ingest/sec/event_extract.py tests/test_sec_event_extract.py
git commit -m "feat: add sec event batch extraction runner"
```

### Task 2: Wire CLI and add batch verification

**Files:**
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/cli.py`
- Modify: `/Users/woody/ai/stockanalysis/tests/test_ingest_cli.py`
- Create: `/Users/woody/ai/stockanalysis/tests/fixtures/sec_filing_aapl_20240629_10q.html`
- Create: `/Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_batch_extract.sh`

**Step 1: Write the failing test**

Add a CLI summary test for `sec-filings-event-batch-extract`.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: FAIL with missing CLI command.

**Step 3: Write minimal implementation**

Implement:
- batch CLI command
- deterministic 10-Q fixture
- docker verify script that proves two SEC filings become two linked events

**Step 4: Run test to verify it passes**

Run:
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- `bash scripts/verify_sec_filings_event_batch_extract.sh`

Expected: both commands pass.

**Step 5: Commit**

```bash
git add src/stockanalysis/ingest/cli.py tests/test_ingest_cli.py tests/fixtures/sec_filing_aapl_20240629_10q.html scripts/verify_sec_filings_event_batch_extract.sh
git commit -m "feat: add sec event batch extract cli"
```

### Task 3: Update operational docs and task artifacts

**Files:**
- Create: `/Users/woody/ai/stockanalysis/docs/sec-filings-event-batch-extract.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-filings-event-batch-extract/contract.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-filings-event-batch-extract/plan.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-filings-event-batch-extract/handoff.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-filings-event-batch-extract/review.md`
- Modify: `/Users/woody/ai/stockanalysis/README.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/verification-plan.md`

**Step 1: Write the failing test**

Define the documentation and task artifacts that explain batch discovery rules, verify command, and next steps.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-event-batch-extract`
Expected: FAIL until task docs exist.

**Step 3: Write minimal implementation**

Add batch docs, task docs, and verification-plan updates.

**Step 4: Run test to verify it passes**

Run:
- `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-event-batch-extract`
- `rg -n "\[[A-Z0-9_]+\]" /Users/woody/ai/stockanalysis/AGENTS.md /Users/woody/ai/stockanalysis/docs -S`

Expected: readiness passes and placeholder search returns no output.

**Step 5: Commit**

```bash
git add docs/sec-filings-event-batch-extract.md docs/tasks/sec-filings-event-batch-extract README.md docs/verification-plan.md
git commit -m "docs: add sec event batch extraction docs"
```
