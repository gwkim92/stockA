# Task Review

## Summary

- Implemented article-quality dedup for the free RSS evidence path.
- Raw HTML extraction now prioritizes article/main/body-like containers and strips common share/comment/navigation boilerplate before chunking.
- Raw-body chunk indexing now skips duplicate raw checksums inside one run and reports skipped duplicate documents.
- AI evidence neighborhood and stock detail read models now deduplicate mirror events by normalized title/source checksum/event id without changing canonical tables.
- Live `/stocks/NVDA` now shows a cleaner evidence relationship section: price chart, AI evidence chunks, and related events are visible from the FastAPI-backed Next cockpit.

## Verification Evidence

- Unit and integration target: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_body_chunk_index tests.test_ai_evidence_graph tests.test_frontend_live_adapter tests.test_ingest_cli -v` passed.
- Script smoke: `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_raw_body_chunk_index.sh` passed.
- Harness: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-article-quality-dedup` passed.
- Harness regression: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-raw-body-chunk-index` passed.
- Frontend build: `cd apps/web && npm run build` passed.
- Whitespace/syntax safety: `git diff --check` passed.
- Live ingest evidence: raw-body chunk-index `run_id=117` completed with `succeeded=10`, `skipped_duplicate_document_count=2`, `failed=0`, `chunk_count=19`, `embedding_count=19`.
- Live API evidence: `/api/ai/evidence-neighborhoods/NVDA?asOfDate=2026-05-20&maxItems=12` returned 12 events and 8 chunks; `/api/stocks/NVDA?asOfDate=2026-05-20` returned 8 recent events after dedup.
- Browser evidence: `/private/tmp/stockanalysis-runtime/stocks-nvda-article-quality-dedup.png`.

## Residual Risks

- This is deterministic local cleanup, not semantic duplicate detection. Articles with different titles/checksums but the same story can still appear separately.
- Read-only SQL dedup improves UI/API quality but intentionally does not delete historical duplicate source documents or chunks.
- Domain-specific page chrome can still leak into chunk previews; future cleanup should add per-domain readability rules and preview QA samples.
- Recommendation quality, thesis generation, live LLM/RAG answer generation, paper execution, and real broker integration were not changed in this task.
