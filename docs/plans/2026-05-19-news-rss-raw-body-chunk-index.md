# News RSS Raw Body Chunk Index Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert stored RSS raw HTML artifacts into local deterministic body-text chunks and embedding metadata for the AI evidence graph.

**Architecture:** Add a Python ingest runner that reads only `file://` raw artifacts under an operator-provided artifact root, extracts readable text with stdlib HTML parsing, splits bounded chunks, and upserts `ai.document_chunk` plus local `ai.embedding_index` metadata. This remains a no-cost/local metadata path, not a semantic vector retrieval implementation.

**Tech Stack:** Python stdlib `html.parser`, Postgres via existing `PsqlCommandExecutor`, `stockanalysis-ingest` CLI, unittest, AWH task docs.

---

### Task 1: Task Contract And Boundaries

**Files:**
- Create: `docs/tasks/news-rss-raw-body-chunk-index/contract.md`
- Create: `docs/tasks/news-rss-raw-body-chunk-index/handoff.md`
- Create: `docs/tasks/news-rss-raw-body-chunk-index/review.md`
- Modify: `docs/verification-plan.md`

**Steps:**
1. Record scope: raw HTML artifact to body text chunks, local deterministic embedding metadata, no external embedding API, no live LLM.
2. Record security boundary: read only `file://` artifacts under `--artifact-root`.
3. Add verification script reference to the verification plan.

### Task 2: Backend Runner

**Files:**
- Create: `src/stockanalysis/ingest/news/raw_body_chunk_index.py`
- Test: `tests/test_news_rss_raw_body_chunk_index.py`

**Steps:**
1. Add candidate SQL for RSS documents with `raw_storage_uri`.
2. Add HTML-to-text extraction and bounded chunking.
3. Add chunk/embedding upsert SQL with local-only/no-cost metadata.
4. Add tests for SQL, extraction, artifact-root guardrail, upsert behavior, and failure status.

### Task 3: CLI Boundary

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Modify: `tests/test_ingest_cli.py`

**Steps:**
1. Add `stockanalysis-ingest news-rss-raw-body-chunk-index`.
2. Expose `--document-limit`, `--external-document-id`, `--artifact-root`, `--provider`, `--model-name`, `--embedding-dimension`, `--max-text-chars`, and `--max-chunks-per-document`.
3. Return non-zero when any document chunking fails.
4. Add CLI dispatch test.

### Task 4: Verification And Live Smoke

**Files:**
- Create: `scripts/verify_news_rss_raw_body_chunk_index.sh`
- Modify: task handoff/review docs

**Steps:**
1. Run targeted tests and verification script.
2. Run AWH task verification.
3. If local DB/env exists, run body chunk index against `/private/tmp/stockanalysis-runtime/news-rss-raw`.
4. Confirm the evidence-neighborhood API now returns raw-body chunk preview metadata for at least one live RSS-backed document.
