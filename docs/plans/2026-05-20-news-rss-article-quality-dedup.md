# News RSS Article Quality Dedup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve free RSS article evidence quality by extracting cleaner article text and suppressing duplicate mirror articles in chunking and UI reads.

**Architecture:** Keep the existing raw fetch and raw-body chunk index boundaries. Add deterministic stdlib HTML cleanup, skip duplicate raw checksums during chunk-index runs, and make read-only AI evidence/stock detail SQL prefer one event/chunk per raw document checksum while still preserving canonical source documents in the database.

**Tech Stack:** Python stdlib `html.parser`, existing Postgres SQL renderers, FastAPI live adapter, Next.js stock detail page, unittest, AWH task docs.

---

### Task 1: Task Contract

**Files:**
- Create: `docs/tasks/news-rss-article-quality-dedup/contract.md`
- Create: `docs/tasks/news-rss-article-quality-dedup/handoff.md`
- Create: `docs/tasks/news-rss-article-quality-dedup/review.md`

**Steps:**
1. Record scope: article text cleanup, checksum duplicate suppression, read-only UI dedup.
2. Record out of scope: schema changes, paid LLM calls, vector DB, recommendation scoring, trading.
3. Record verification commands and live smoke target.

### Task 2: Article Text Cleanup

**Files:**
- Modify: `src/stockanalysis/ingest/news/raw_body_chunk_index.py`
- Modify: `tests/test_news_rss_raw_body_chunk_index.py`

**Steps:**
1. Add tests for preferring `<article>`/`<main>` text over nav/header/footer text.
2. Add tests for trimming common social/share/comment boilerplate from the beginning and end.
3. Implement a small stdlib HTML extractor that tracks candidate containers and returns the best article-like body.
4. Keep metadata fallback when no readable body remains.

### Task 3: Duplicate Suppression

**Files:**
- Modify: `src/stockanalysis/ingest/news/raw_body_chunk_index.py`
- Modify: `tests/test_news_rss_raw_body_chunk_index.py`
- Modify: `src/stockanalysis/ai/evidence_graph.py`
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `tests/test_ai_evidence_graph.py`
- Modify: `tests/test_frontend_live_adapter.py`

**Steps:**
1. Skip duplicate candidates by raw checksum within a chunk-index run and report `skipped_duplicate_document_count`.
2. Add metadata showing duplicate skip reason without deleting canonical source documents.
3. Deduplicate evidence-neighborhood events/chunks by `source_document.checksum` in read-only SQL.
4. Deduplicate stock-detail related events by `source_document.checksum` in read-only SQL.

### Task 4: Verification And Live Smoke

**Files:**
- Modify: `docs/tasks/news-rss-article-quality-dedup/handoff.md`
- Modify: `docs/tasks/news-rss-article-quality-dedup/review.md`

**Steps:**
1. Run targeted Python tests for RSS raw body, AI evidence SQL, and live adapter.
2. Run `scripts/verify_news_rss_raw_body_chunk_index.sh`.
3. Run AWH verification for the new task and existing raw-body chunk task.
4. Re-run local live raw-body chunk index against direct RSS artifacts with `--exclude-url-host news.google.com`.
5. Verify `/stocks/NVDA` still renders and no longer starts with repeated mirror chunks/events.
