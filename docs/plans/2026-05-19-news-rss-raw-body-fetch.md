# News RSS Raw Body Fetch Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Persist free public RSS article bodies as local raw artifacts and attach them to `ingest.source_document.raw_storage_uri`.

**Architecture:** Add a backend ingest runner under `stockanalysis.ingest.news` that discovers `news_rss_item` source documents, fetches bounded public HTTP/HTTPS article HTML, writes repo-outside artifacts, and updates the existing document boundary. Keep this as a data collection step only; raw article text indexing and semantic retrieval quality are follow-up slices.

**Tech Stack:** Python stdlib HTTP fetch, Postgres via existing `PsqlCommandExecutor`, `stockanalysis-ingest` CLI, unittest, AWH task docs.

---

### Task 1: Task Contract And Boundaries

**Files:**
- Create: `docs/tasks/news-rss-raw-body-fetch/contract.md`
- Create: `docs/tasks/news-rss-raw-body-fetch/handoff.md`
- Create: `docs/tasks/news-rss-raw-body-fetch/review.md`
- Modify: `docs/verification-plan.md`

**Steps:**
1. Record scope: free RSS public article body fetch, raw artifact persistence, DB metadata update, no paid API, no live LLM, no trading.
2. Record security boundary: only `http`/`https`, reject localhost/private IP literal URLs, bounded body size, no secret output.
3. Add verification script reference to the verification plan.

### Task 2: Backend Runner

**Files:**
- Create: `src/stockanalysis/ingest/news/raw_fetch.py`
- Test: `tests/test_news_rss_raw_fetch.py`

**Steps:**
1. Add SQL renderer to discover pending `news_rss_item` source documents.
2. Add public URL validation and redirect validation before fetch.
3. Add bounded article body fetch/write/update workflow with `ops.pipeline_run` tracking.
4. Add unit tests for SQL shape, successful artifact write/update, skip behavior, failure status, and blocked private/local URLs.

### Task 3: CLI Boundary

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Modify: `tests/test_ingest_cli.py`

**Steps:**
1. Add `stockanalysis-ingest news-rss-raw-fetch`.
2. Expose `--limit`, `--external-document-id`, `--artifact-root`, `--body-file`, `--force`, `--max-body-bytes`, and `--user-agent`.
3. Return non-zero when any document fetch/update fails.
4. Add CLI dispatch test.

### Task 4: Verification

**Files:**
- Create: `scripts/verify_news_rss_raw_body_fetch.sh`

**Steps:**
1. Run py_compile for the new runner and CLI.
2. Run targeted unit tests.
3. Check docs/task files exist.
4. Check SQL/fetch/security markers exist.
5. Run AWH task verification.

### Task 5: Local Live Smoke

**Files:**
- Modify: `docs/tasks/news-rss-raw-body-fetch/handoff.md`
- Modify: `docs/tasks/news-rss-raw-body-fetch/review.md`

**Steps:**
1. If local DB/env is available, run a small bounded fetch with `--limit 2` and artifact root under `/private/tmp/stockanalysis-runtime`.
2. Record success/failure counts without printing secrets.
3. Leave follow-up: raw artifact body extraction into document chunks.
