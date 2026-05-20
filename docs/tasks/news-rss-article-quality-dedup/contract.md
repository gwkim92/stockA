# Task Contract

## Task

- 이름: news-rss-article-quality-dedup
- 요청: 직접 RSS 기사 원문 증거에서 페이지 boilerplate와 mirror 중복을 줄여 사람이 읽을 수 있는 AI/RAG 근거 품질을 개선한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - raw HTML chunk index는 `<article>`/`<main>` 같은 기사 본문 후보를 우선 사용한다.
  - raw HTML chunk index는 흔한 공유/댓글/navigation boilerplate를 chunk preview에서 줄인다.
  - 같은 raw checksum을 가진 mirror 문서는 한 chunk-index 실행 안에서 중복 upsert하지 않고 skip으로 보고한다.
  - AI evidence neighborhood와 stock detail read-only SQL은 `source_document.checksum` 기준으로 mirror event/chunk를 dedup해서 보여준다.
  - 외부 유료 API, live LLM, 추천 점수, trading flow는 호출하지 않는다.

## Scope

- 포함:
  - stdlib HTML article-like text extraction refinement
  - local raw checksum duplicate skip in `news-rss-raw-body-chunk-index`
  - read-only SQL dedup in AI evidence graph and stock detail
  - targeted unit tests
  - AWH task docs and live local smoke when runtime is available
- 제외:
  - DB migration
  - semantic vector similarity ranking
  - paid or external embedding API call
  - live LLM analysis
  - recommendation scoring, benchmark, evaluation split 변경
  - broker/order/write API 변경
  - scheduler host activation

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/raw_body_chunk_index.py`
  - `src/stockanalysis/ai/evidence_graph.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_news_rss_raw_body_chunk_index.py`
  - `tests/test_ai_evidence_graph.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/plans/2026-05-20-news-rss-article-quality-dedup.md`
  - `docs/tasks/news-rss-article-quality-dedup/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_body_chunk_index tests.test_ai_evidence_graph tests.test_frontend_live_adapter -v`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_raw_body_chunk_index.sh`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_cli -v`
  - `cd apps/web && npm run typecheck`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-article-quality-dedup`
  - `git diff --check`

## Done Criteria

- [x] article-like text extraction tests pass.
- [x] raw checksum duplicate skip tests pass.
- [x] read-only AI evidence and stock detail SQL include checksum dedup.
- [x] targeted tests and AWH verification pass.
- [x] live local smoke confirms fewer duplicate NVIDIA mirror chunks/events in `/stocks/NVDA`.
