# Review

## Summary

- Added `src/stockanalysis/ingest/news/chunk_index.py` as a backend runner for local/free RSS document chunk and embedding metadata generation.
- Added `stockanalysis-ingest news-rss-local-chunk-index` so this is a real backend operation, not another product shell script.
- The runner writes `ai.document_chunk` and `ai.embedding_index`, records `ops.pipeline_run`, and redacts operational output to counts/provider/model only.
- It uses `local_deterministic` metadata and no external embedding API, vector DB, or live LLM call.
- Added stale same-provider/model embedding cleanup so content hash changes do not duplicate evidence neighborhood rows.
- Ran the live local DB backfill and verified `/stocks/NVDA` now shows the RSS source chunk and embedding status.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_chunk_index tests.test_ingest_cli.IngestCliTests.test_news_rss_local_chunk_index_cli_prints_summary -v`: 5 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_local_chunk_index.sh`: passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_cli tests.test_news_rss tests.test_news_rss_chunk_index -v`: 56 tests passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-local-chunk-index`: passed readiness checks.
- `git diff --check`: passed.
- Live local CLI run: candidate documents 40, chunks 40, embeddings 40, stale embeddings deleted 40, run_id 98, status completed.
- Live FastAPI smoke: `NVDA` evidence neighborhood reports event 1, AI artifact 1, evidence chunk 1, embedded chunk 1, provider `local_deterministic`, live LLM false.
- Browser smoke: `/stocks/NVDA` renders `AI 증거 관계망`, chunk count 1, embedding status, normal preview text, and the no-live-LLM guardrail.

## Residual Risks

- This is not semantic vector similarity yet. The embedding row is a deterministic local metadata placeholder for free MVP visibility.
- The current chunk text is limited to title, summary, and URL because RSS bodies are not fetched.
- This does not change recommendation scoring, thesis quality, paper/live trading, benchmark, or evaluation split.
- A future task should decide between richer free article fetching/readability extraction, semantic local embeddings, or a dedicated cross-news AI evidence page.
