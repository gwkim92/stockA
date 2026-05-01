# SEC Filings Event Extraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first deterministic pipeline that turns a raw SEC filing artifact into an `event.event` row linked to its source document.

**Architecture:** Read a single SEC `source_document` row by accession number, load the raw artifact via `raw_storage_uri`, derive a heuristic event candidate from the filing form and body excerpt, then upsert `event.event` and `event.event_document_link` in one SQL transaction. Keep scope intentionally narrow: single-document extraction only, no LLM, no impact mapping.

**Tech Stack:** Python 3, built-in `html.parser`, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: Add event extraction models and SQL

**Files:**
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/models.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/sql.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_sec_event_extract.py`

**Step 1: Write the failing test**

Write tests that expect:
- a source document lookup record to deserialize correctly
- an extracted event candidate for a `10-K`
- SQL output to contain `event.event` and `event.event_document_link`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: FAIL with missing SEC event extraction models or SQL helpers.

**Step 3: Write minimal implementation**

Add:
- `SecEventSourceDocumentRecord`
- `SecExtractedEventCandidate`
- `SecEventExtractionResult`
- source document lookup SQL
- event upsert SQL with dedupe key conflict handling

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: SEC event extraction tests pass.

**Step 5: Commit**

```bash
git add src/stockanalysis/ingest/sec/models.py src/stockanalysis/ingest/sec/sql.py tests/test_sec_event_extract.py
git commit -m "feat: add sec filing event extraction sql"
```

### Task 2: Implement single-document event extraction runner and CLI

**Files:**
- Create: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/event_extract.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/cli.py`
- Modify: `/Users/woody/ai/stockanalysis/tests/test_ingest_cli.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_sec_event_extract.py`

**Step 1: Write the failing test**

Add tests that expect:
- pipeline run lifecycle for successful extraction
- failed run status when event upsert errors
- CLI summary JSON for `sec-filings-event-extract`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: FAIL with missing `run_sec_filings_event_extract` or CLI command.

**Step 3: Write minimal implementation**

Implement:
- source document lookup by accession number
- raw artifact text extraction from local file URI
- heuristic form-type mapping to event candidate
- pipeline run create/succeed/fail
- CLI command wiring

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: all SEC event extraction unit tests pass.

**Step 5: Commit**

```bash
git add src/stockanalysis/ingest/sec/event_extract.py src/stockanalysis/ingest/cli.py tests/test_ingest_cli.py tests/test_sec_event_extract.py
git commit -m "feat: add sec filing event extraction runner"
```

### Task 3: Add integration verify and docs

**Files:**
- Create: `/Users/woody/ai/stockanalysis/scripts/verify_sec_filings_event_extract.sh`
- Create: `/Users/woody/ai/stockanalysis/docs/sec-filings-event-extraction.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-filings-event-extraction/contract.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-filings-event-extraction/plan.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-filings-event-extraction/handoff.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-filings-event-extraction/review.md`
- Modify: `/Users/woody/ai/stockanalysis/README.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/verification-plan.md`

**Step 1: Write the failing test**

Define a Docker-based verify script that:
- seeds the DB
- upserts SEC filing metadata
- fetches a raw filing artifact
- extracts an event
- asserts event row, dedupe key, and succeeded pipeline run

**Step 2: Run test to verify it fails**

Run: `bash scripts/verify_sec_filings_event_extract.sh`
Expected: FAIL until the event extraction pipeline is fully wired.

**Step 3: Write minimal implementation**

Add the verify script and operational docs describing mapping, limits, and next steps.

**Step 4: Run test to verify it passes**

Run:
- `bash scripts/verify_sec_filings_event_extract.sh`
- `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-filings-event-extraction`

Expected: both commands pass.

**Step 5: Commit**

```bash
git add scripts/verify_sec_filings_event_extract.sh docs/sec-filings-event-extraction.md docs/tasks/sec-filings-event-extraction README.md docs/verification-plan.md
git commit -m "docs: add sec filings event extraction verification"
```
