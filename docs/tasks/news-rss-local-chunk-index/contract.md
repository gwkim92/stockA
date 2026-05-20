# Task Contract

## Task

- 이름: news-rss-local-chunk-index
- 요청: RSS 뉴스 원천 문서가 AI 증거 관계망에서 RAG 준비 상태로 보이도록 무료 로컬 document chunk와 embedding index metadata를 생성한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `news_rss_item` source document를 대상으로 `ai.document_chunk`와 `ai.embedding_index` rows를 생성하는 backend runner가 존재한다.
  - 외부 embedding API, 유료 vector DB, live LLM call 없이 deterministic local metadata만 저장한다.
  - 기존 `/api/ai/evidence-neighborhoods/{symbol}`가 RSS 문서 chunk/embedding 상태를 보여줄 수 있다.
  - CLI는 shell script product orchestration이 아니라 `stockanalysis-ingest` backend boundary를 통해 실행된다.

## Scope

- 포함:
  - RSS source document chunk/index SQL renderer
  - backend runner with `ops.pipeline_run` tracking
  - `stockanalysis-ingest news-rss-local-chunk-index` CLI
  - targeted unit tests and verification script
  - live local DB smoke and browser/UI confirmation when runtime is available
  - task handoff/review 문서
- 제외:
  - DB migration
  - pgvector, external vector DB, GraphDB, OpenAI vector store
  - paid or external embedding API call
  - live LLM analysis
  - recommendation scoring, benchmark, evaluation split 변경
  - broker/order/write API 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/chunk_index.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_news_rss_chunk_index.py`
  - `tests/test_ingest_cli.py`
  - `scripts/verify_news_rss_local_chunk_index.sh`
  - `docs/verification-plan.md`
  - `docs/tasks/news-rss-local-chunk-index/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_chunk_index tests.test_ingest_cli -v`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_local_chunk_index.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-local-chunk-index`
  - `git diff --check`

## Done Criteria

- [x] deterministic local chunk/index runner exists.
- [x] CLI command prints a redacted summary and records pipeline status.
- [x] tests cover SQL boundary, local/no-cost provider metadata, failure handling, and CLI dispatch.
- [x] live local DB smoke shows non-zero chunk/index counts when RSS documents exist.
- [x] handoff/review record exact verification evidence and residual risks.

## Verification Evidence

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_chunk_index tests.test_ingest_cli.IngestCliTests.test_news_rss_local_chunk_index_cli_prints_summary -v`
  - result: 5 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_local_chunk_index.sh`
  - result: passed and printed `news RSS local chunk index verification passed`.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_cli tests.test_news_rss tests.test_news_rss_chunk_index -v`
  - result: 56 tests passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-local-chunk-index`
  - result: task passed readiness checks.
- `git diff --check`
  - result: passed.
- Live local DB run:
  - command: `stockanalysis-ingest news-rss-local-chunk-index --document-limit 50`
  - result: candidate documents 40, chunks 40, embeddings 40, stale embeddings deleted 40, run_id 98, status completed.
- Live FastAPI smoke:
  - endpoint: `/api/ai/evidence-neighborhoods/NVDA?asOfDate=2026-05-19&maxItems=12`
  - result: event 1, AI artifact 1, evidence chunk 1, embedded chunk 1, provider `local_deterministic`, live LLM false.
- Browser smoke:
  - URL: `http://127.0.0.1:3001/stocks/NVDA`
  - result: visible `AI 증거 관계망`, chunk count 1, embedding status, no-live-LLM guardrail, and preview text.
