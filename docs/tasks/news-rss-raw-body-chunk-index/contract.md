# Task Contract

## Task

- 이름: news-rss-raw-body-chunk-index
- 요청: 저장된 RSS raw HTML artifact를 본문 텍스트 chunk로 변환해 AI 증거 관계망에서 title/summary보다 나은 근거를 보여준다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `raw_storage_uri`가 있는 RSS source document를 대상으로 본문 텍스트 chunk를 생성하는 backend runner가 존재한다.
  - runner는 `file://` artifact를 `--artifact-root` 아래에서만 읽는다.
  - `ai.document_chunk`와 `ai.embedding_index`에는 local deterministic metadata만 저장된다.
  - 외부 embedding API, 유료 vector DB, live LLM call은 사용하지 않는다.

## Scope

- 포함:
  - raw HTML artifact candidate lookup SQL
  - stdlib HTML text extraction
  - bounded chunk splitting
  - local deterministic chunk/index upsert SQL
  - `stockanalysis-ingest news-rss-raw-body-chunk-index` CLI
  - targeted unit tests and verification script
  - live local DB smoke if runtime is available
- 제외:
  - DB migration
  - semantic vector similarity ranking
  - paid or external embedding API call
  - live LLM analysis
  - recommendation scoring, benchmark, evaluation split 변경
  - broker/order/write API 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/raw_body_chunk_index.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_news_rss_raw_body_chunk_index.py`
  - `tests/test_ingest_cli.py`
  - `scripts/verify_news_rss_raw_body_chunk_index.sh`
  - `docs/verification-plan.md`
  - `docs/plans/2026-05-19-news-rss-raw-body-chunk-index.md`
  - `docs/tasks/news-rss-raw-body-chunk-index/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_body_chunk_index tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_body_chunk_index_cli_prints_summary -v`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_raw_body_chunk_index.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-raw-body-chunk-index`
  - `git diff --check`

## Done Criteria

- [x] raw body chunk index runner exists.
- [x] CLI command prints a redacted summary and records pipeline status.
- [x] tests cover SQL boundary, HTML extraction, artifact-root guardrail, local/no-cost provider metadata, failure handling, metadata fallback, and CLI dispatch.
- [x] live local DB smoke updates at least one RSS raw artifact document chunk when runtime is available.
- [x] handoff/review record exact verification evidence and residual risks.

## Verification Evidence

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_body_chunk_index tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_body_chunk_index_cli_prints_summary -v`
  - result: 10 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_raw_body_chunk_index.sh`
  - result: passed and printed `news RSS raw body chunk index verification passed`.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-raw-body-chunk-index`
  - result: task passed readiness checks.
- Live local DB run:
  - command: `stockanalysis-ingest news-rss-raw-body-chunk-index --document-limit 3 --artifact-root /private/tmp/stockanalysis-runtime/news-rss-raw --max-text-chars 1200 --max-chunks-per-document 3`
  - result: run_id 103, requested 3, succeeded 3, failed 0, chunks 3, embeddings 3, model `rss_raw_html_text_hash_v1`, no external embedding API, no live LLM.
- Live FastAPI smoke:
  - endpoint: `/api/ai/evidence-neighborhoods/NVDA?asOfDate=2026-05-19&maxItems=12`
  - result: chunk count 1, embedded chunk count 1, provider `local_deterministic`, model `rss_raw_html_text_hash_v1`, preview starts with the Nvidia H200 article title.
- Browser smoke:
  - URL: `http://127.0.0.1:3001/stocks/NVDA`
  - result: visible `AI 증거 관계망`, `rss_raw_html_text_hash_v1`, and Nvidia H200 evidence preview.
  - screenshot: `/private/tmp/stockanalysis-runtime/stocks-nvda-raw-body-chunk.png`
