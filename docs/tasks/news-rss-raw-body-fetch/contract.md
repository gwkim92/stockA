# Task Contract

## Task

- 이름: news-rss-raw-body-fetch
- 요청: RSS 뉴스 원천 문서의 기사 본문 HTML을 무료 공개 URL에서 가져와 raw artifact로 저장하고 DB 문서에 연결한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `news_rss_item` source document 후보를 찾는 backend runner가 존재한다.
  - runner는 기사 URL을 fetch해 local artifact에 저장하고 `ingest.source_document.raw_storage_uri`를 갱신한다.
  - 실행 이력은 `ops.pipeline_run`에 남는다.
  - 외부 유료 API, live LLM, embedding API, trading flow는 호출하지 않는다.
  - SSRF 위험을 줄이기 위해 `http`/`https`만 허용하고 localhost/private IP literal URL은 거부한다.

## Scope

- 포함:
  - RSS source document raw body fetch SQL renderer
  - public article fetch URL validation and bounded body read
  - local artifact write and source document metadata update
  - `stockanalysis-ingest news-rss-raw-fetch` CLI
  - targeted unit tests and verification script
  - task handoff/review 문서
- 제외:
  - DB migration
  - article text extraction/chunking from raw HTML
  - paid news provider API
  - semantic vector retrieval quality
  - live LLM analysis
  - recommendation scoring, benchmark, evaluation split 변경
  - broker/order/write API 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/raw_fetch.py`
  - `src/stockanalysis/ingest/cli.py`
  - `tests/test_news_rss_raw_fetch.py`
  - `tests/test_ingest_cli.py`
  - `scripts/verify_news_rss_raw_body_fetch.sh`
  - `docs/verification-plan.md`
  - `docs/plans/2026-05-19-news-rss-raw-body-fetch.md`
  - `docs/tasks/news-rss-raw-body-fetch/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_fetch tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_fetch_cli_prints_summary -v`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_raw_body_fetch.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-raw-body-fetch`
  - `git diff --check`

## Done Criteria

- [x] raw body fetch runner exists.
- [x] CLI command prints a redacted summary and records pipeline status.
- [x] tests cover SQL boundary, artifact write/update, failure handling, CLI dispatch, and blocked unsafe URLs.
- [x] handoff/review record exact verification evidence and residual risks.

## Verification Evidence

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_fetch tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_fetch_cli_prints_summary -v`
  - result: 10 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_raw_body_fetch.sh`
  - result: passed and printed `news RSS raw body fetch verification passed`.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-raw-body-fetch`
  - result: task passed readiness checks.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_cli -v`
  - result: 47 tests passed.
- `git diff --check`
  - result: passed.
- Live local DB smoke:
  - command: `stockanalysis-ingest news-rss-raw-fetch --limit 2 --artifact-root /private/tmp/stockanalysis-runtime/news-rss-raw --max-body-bytes 300000`
  - result: run_id 99, requested 2, succeeded 2, failed 0, paid provider API false, live LLM false.
- Live naming smoke after extension fix:
  - command: `stockanalysis-ingest news-rss-raw-fetch --limit 1 --artifact-root /private/tmp/stockanalysis-runtime/news-rss-raw --max-body-bytes 200000`
  - result: run_id 100, requested 1, succeeded 1, failed 0, artifact path ended in `.html`.
