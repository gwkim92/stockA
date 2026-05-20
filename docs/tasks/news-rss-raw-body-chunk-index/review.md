# Task Review

## Summary

- Added RSS raw-body chunk indexing as a backend AI metadata boundary.
- The runner reads only `file://` artifacts under `--artifact-root`, extracts text via stdlib HTML parsing, falls back explicitly to source document metadata when raw HTML has no readable text, and upserts `ai.document_chunk` plus local deterministic `ai.embedding_index` rows.
- Added `stockanalysis-ingest news-rss-raw-body-chunk-index` CLI with non-zero exit on failed documents.
- Added `--exclude-url-host` so direct publisher artifacts can be indexed without reselecting stale Google News intermediary documents.
- Frontend AI evidence/stock detail reads now down-rank Google News intermediary evidence and show source host plus whether the chunk came from raw HTML or metadata fallback.
- No paid provider API, live LLM call, semantic vector DB, recommendation scoring, or trading behavior was added.

## Verification Evidence

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_body_chunk_index tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_body_chunk_index_cli_prints_summary -v`: 10 tests passed before host exclusion.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_fetch tests.test_news_rss_raw_body_chunk_index tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_fetch_cli_prints_summary tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_body_chunk_index_cli_prints_summary -v`: 22 tests passed after host exclusion.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_raw_body_chunk_index.sh`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-raw-body-chunk-index`: passed readiness checks.
- Live local DB run_id 103: requested 3, succeeded 3, failed 0, chunk count 3, embedding count 3, no external embedding API, no live LLM.
- Live local DB run_id 112: requested 12, succeeded 12, failed 0, chunk count 36, embedding count 36, all first-batch chunks came from direct raw HTML text.
- Live enrichment run_id 113: classified 79 RSS events and linked 23 events to instruments with local rules.
- Live cluster evidence run_id 114: inserted 5 local AI evidence artifacts.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ai_evidence_graph tests.test_frontend_live_adapter -v`: 40 tests passed.
- `cd apps/web && npm run typecheck`: passed.
- Live FastAPI smoke for `/api/ai/evidence-neighborhoods/NVDA?asOfDate=2026-05-19&maxItems=12`: provider `local_deterministic`, model `rss_raw_html_text_hash_v1`, embedded chunk count 1.
- Browser smoke for `/stocks/NVDA`: `AI 증거 관계망`, `rss_raw_html_text_hash_v1`, and Nvidia H200 preview are visible.
- Browser smoke after direct feed rerun: `/stocks/NVDA` shows direct NVIDIA events first and evidence chunks labeled `blogs.nvidia.com · 원문 본문 추출`; screenshot saved at `/private/tmp/stockanalysis-runtime/stocks-nvda-direct-evidence.png`.

## Residual Risks

- Older Google News RSS documents remain in the local DB, but current evidence/stock detail queries down-rank them and direct feed runs use host exclusion.
- Direct feeds can duplicate the same article across mirrored NVIDIA feeds; deduplication is still needed.
- This creates local deterministic embedding metadata only; it still does not provide semantic similarity ranking.
- Raw HTML still includes page boilerplate; article body extraction should be cleaned before these chunks become recommendation-quality evidence.
