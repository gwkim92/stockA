# Event Classification Impact Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first bootstrap pipeline that creates a minimal internal reporting taxonomy and links existing SEC events to classification nodes in `event.event_classification_impact`.

**Architecture:** Reuse the existing SEC event pipeline as the source of event rows, discover SEC events that do not yet have classification impacts, bootstrap a small `internal_theme` taxonomy in `ref.classification_node`/`ref.classification_edge`, then upsert `event.event_classification_impact` rows. Keep scope intentionally narrow: deterministic mappings only, no LLM enrichment, no instrument impacts.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: Add impact bootstrap models and SQL

**Files:**
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/models.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/sql.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_sec_classification_impact.py`

**Step 1: Write the failing test**

Add tests for:
- pending SEC event discovery
- classification bootstrap SQL
- impact upsert SQL

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: FAIL with missing classification impact helpers.

**Step 3: Write minimal implementation**

Add:
- event impact candidate/result models
- pending SEC event lookup SQL
- internal reporting taxonomy bootstrap SQL
- event classification impact upsert SQL

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: classification impact unit tests pass.

**Step 5: Commit**

```bash
git add src/stockanalysis/ingest/sec/models.py src/stockanalysis/ingest/sec/sql.py tests/test_sec_classification_impact.py
git commit -m "feat: add event classification impact sql"
```

### Task 2: Implement bootstrap runner and CLI

**Files:**
- Create: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/classification_impact.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/cli.py`
- Modify: `/Users/woody/ai/stockanalysis/tests/test_ingest_cli.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_sec_classification_impact.py`

**Step 1: Write the failing test**

Add tests that expect:
- pending event bootstrap runner summary
- continue-on-error behavior
- CLI summary for `event-classification-impact-bootstrap`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: FAIL with missing runner or CLI command.

**Step 3: Write minimal implementation**

Implement:
- pending SEC event discovery
- one-shot taxonomy bootstrap
- per-event impact upsert
- bootstrap pipeline run lifecycle
- CLI wiring

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`
Expected: all classification impact tests pass.

**Step 5: Commit**

```bash
git add src/stockanalysis/ingest/sec/classification_impact.py src/stockanalysis/ingest/cli.py tests/test_ingest_cli.py tests/test_sec_classification_impact.py
git commit -m "feat: add event classification impact bootstrap"
```

### Task 3: Add integration verify and operational docs

**Files:**
- Create: `/Users/woody/ai/stockanalysis/scripts/verify_event_classification_impact_bootstrap.sh`
- Create: `/Users/woody/ai/stockanalysis/docs/event-classification-impact-bootstrap.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/event-classification-impact-bootstrap/contract.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/event-classification-impact-bootstrap/plan.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/event-classification-impact-bootstrap/handoff.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/event-classification-impact-bootstrap/review.md`
- Modify: `/Users/woody/ai/stockanalysis/README.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/verification-plan.md`

**Step 1: Write the failing test**

Define a Docker-based verify script that:
- seeds the DB
- creates SEC events
- runs classification impact bootstrap
- asserts taxonomy nodes, edges, and event impact rows

**Step 2: Run test to verify it fails**

Run: `bash scripts/verify_event_classification_impact_bootstrap.sh`
Expected: FAIL until the bootstrap pipeline is wired.

**Step 3: Write minimal implementation**

Add the verify script and docs describing taxonomy bootstrap, event mappings, limits, and next steps.

**Step 4: Run test to verify it passes**

Run:
- `bash scripts/verify_event_classification_impact_bootstrap.sh`
- `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task event-classification-impact-bootstrap`

Expected: both commands pass.

**Step 5: Commit**

```bash
git add scripts/verify_event_classification_impact_bootstrap.sh docs/event-classification-impact-bootstrap.md docs/tasks/event-classification-impact-bootstrap README.md docs/verification-plan.md
git commit -m "docs: add event classification impact bootstrap docs"
```
