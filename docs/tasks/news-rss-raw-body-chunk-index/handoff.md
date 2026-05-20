# Session Handoff

## Active Task

- 이름: news-rss-raw-body-chunk-index
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract created.
  - backend raw body chunk index runner created in `src/stockanalysis/ingest/news/raw_body_chunk_index.py`.
  - `stockanalysis-ingest news-rss-raw-body-chunk-index` CLI added.
  - targeted tests and verification script added.
  - live local DB run created 3 chunks and 3 local deterministic embedding metadata rows.
  - `/stocks/NVDA` browser smoke confirmed the raw-body model evidence preview is rendered.
  - added `--exclude-url-host` so raw-body indexing can skip stale Google News intermediary artifacts.
  - live DB run_id 112 indexed 12 direct raw HTML documents, creating 36 chunks and 36 local deterministic embedding metadata rows with `source_text_kind=raw_html_text`.
  - news RSS enrichment run_id 113 linked 23 events to instruments, and cluster evidence run_id 114 inserted 5 local AI evidence artifacts.
  - FastAPI and Next.js browser smoke confirmed `/stocks/NVDA` shows direct NVIDIA evidence chunks before older Google intermediary evidence.
- 진행 중:
  - none for this task.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: add article boilerplate cleanup/deduplication and improve event/theme display so users can see why similar NVIDIA items are repeated.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_body_chunk_index tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_body_chunk_index_cli_prints_summary -v`: 10 tests passed before host exclusion.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_fetch tests.test_news_rss_raw_body_chunk_index tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_fetch_cli_prints_summary tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_body_chunk_index_cli_prints_summary -v`: 22 tests passed after host exclusion.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_raw_body_chunk_index.sh`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-raw-body-chunk-index`: passed readiness checks.
- Live CLI run_id 103: requested 3, succeeded 3, failed 0, chunks 3, embeddings 3.
- Live CLI run_id 112: `--exclude-url-host news.google.com`, requested 12, succeeded 12, failed 0, chunks 36, embeddings 36, all first-batch results used `raw_html_text`.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ai_evidence_graph tests.test_frontend_live_adapter -v`: 40 tests passed after frontend evidence ordering/payload changes.
- `cd apps/web && npm run typecheck`: passed.
- Live FastAPI smoke for `NVDA`: model `rss_raw_html_text_hash_v1`, provider `local_deterministic`, embedded chunk count 1.
- Browser smoke for `http://127.0.0.1:3001/stocks/NVDA`: AI evidence section showed the Nvidia H200 preview and raw-body model id.
- Screenshot saved at `/private/tmp/stockanalysis-runtime/stocks-nvda-raw-body-chunk.png`.
- Browser smoke after direct feed rerun saved `/private/tmp/stockanalysis-runtime/stocks-nvda-direct-evidence.png`; visible evidence chunks show `blogs.nvidia.com · 원문 본문 추출`.

## Risks

- Raw HTML can still include publisher page boilerplate before and after the actual article body.
- This remains deterministic local metadata and does not provide semantic vector similarity quality.
- Artifact-root validation prevents arbitrary local file reads but requires operators to pass the same root used by raw fetch.
- Duplicate direct feeds can produce repeated chunks for the same underlying NVIDIA article.
- Older Google News intermediary chunks remain in the DB but are down-ranked in the current AI evidence and stock detail queries.
