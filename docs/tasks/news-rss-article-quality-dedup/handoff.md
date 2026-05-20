# Session Handoff

## Active Task

- 이름: news-rss-article-quality-dedup
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract created.
  - `raw_body_chunk_index.py` now prefers article-like HTML containers (`article`, `main`, article/body/content class or role markers) before falling back to full-page text.
  - Common sharing/comment/navigation boilerplate is removed from extracted raw-body chunk text.
  - One raw-body chunk-index run now skips repeated `source_document.checksum` values and reports `skipped_duplicate_document_count`.
  - AI evidence neighborhood SQL and stock detail SQL now deduplicate read models by normalized title, source checksum, or event id while downranking Google News mirrors.
  - `/stocks/NVDA` was checked in the browser; the page renders live price chart, AI evidence relationship, evidence chunks, and deduplicated related events.
- 진행 중:
  - none.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: build the next quality slice for domain-specific article cleanup and semantic duplicate grouping, or move to the recommendation/thesis quality evaluation slice if article evidence quality is acceptable.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_body_chunk_index tests.test_ai_evidence_graph tests.test_frontend_live_adapter tests.test_ingest_cli -v` passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_raw_body_chunk_index.sh` passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-article-quality-dedup` passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-raw-body-chunk-index` passed.
- `cd apps/web && npm run build` passed.
- `git diff --check` passed.
- Live raw-body chunk-index run `run_id=117` completed with `succeeded=10`, `skipped_duplicate_document_count=2`, `failed=0`, `chunk_count=19`, `embedding_count=19`.
- FastAPI smoke showed `/api/ai/evidence-neighborhoods/NVDA` returning 12 events and 8 chunks, and `/api/stocks/NVDA` returning 8 recent events after dedup.
- Browser evidence: `/private/tmp/stockanalysis-runtime/stocks-nvda-article-quality-dedup.png`.

## Risks

- Generic HTML cleanup can remove useful publisher text if too aggressive.
- Checksum dedup suppresses mirrored raw pages with identical raw content but not semantically duplicate articles with different titles, chrome, or checksums.
- Older duplicate chunks can remain in the database; read-only SQL dedup now reduces UI noise but does not delete historical data.
- Some publisher boilerplate can still appear in domains with non-standard article markup; this should be handled with domain-specific cleanup or richer readability scoring later.
