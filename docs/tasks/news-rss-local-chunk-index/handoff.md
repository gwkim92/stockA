# Session Handoff

## Active Task

- 이름: news-rss-local-chunk-index
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract created.
- deterministic RSS source document chunk/index backend runner created in `src/stockanalysis/ingest/news/chunk_index.py`.
- `stockanalysis-ingest news-rss-local-chunk-index` CLI added.
- verification script `scripts/verify_news_rss_local_chunk_index.sh` added and referenced from `docs/verification-plan.md`.
- local live DB run completed for 40 RSS documents.
- `/stocks/NVDA` browser smoke confirms the AI evidence neighborhood now shows chunk and embedding readiness.
- 진행 중:
  - none for this task.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: decide whether to add real semantic retrieval ranking over these local chunks, or first expose a dedicated AI/news evidence page showing related event clusters across symbols.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_chunk_index tests.test_ingest_cli.IngestCliTests.test_news_rss_local_chunk_index_cli_prints_summary -v`: 5 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_local_chunk_index.sh`: passed.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_cli tests.test_news_rss tests.test_news_rss_chunk_index -v`: 56 tests passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-local-chunk-index`: passed readiness checks.
- `git diff --check`: passed.
- Live CLI run: candidate documents 40, chunks 40, embeddings 40, stale embeddings deleted 40, run_id 98, status completed.
- Live FastAPI smoke for `NVDA`: `evidence_chunk_count=1`, `embedded_chunk_count=1`, `embedding_provider=local_deterministic`, `live_llm=false`.
- Browser smoke for `http://127.0.0.1:3001/stocks/NVDA`: `AI 증거 관계망`, chunk count 1, embedding status, preview text, and no-live-LLM guardrail are visible.

## Risks

- This task creates local metadata only. It does not create semantic vector similarity quality.
- `ai.embedding_index.vector_storage_uri` will point to a local deterministic placeholder, not an external vector store.
- Recommendation scoring and trading flows remain unchanged.
- Existing rows from a previous buggy regex run were corrected by deleting stale same-provider/model embedding rows whose content hash no longer matches the chunk.
