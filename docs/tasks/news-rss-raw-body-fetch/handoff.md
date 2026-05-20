# Session Handoff

## Active Task

- 이름: news-rss-raw-body-fetch
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract created.
  - backend raw body fetch runner created in `src/stockanalysis/ingest/news/raw_fetch.py`.
  - `stockanalysis-ingest news-rss-raw-fetch` CLI added.
  - targeted tests and verification script added.
  - local live DB smoke fetched 3 RSS article bodies into `/private/tmp/stockanalysis-runtime/news-rss-raw`.
  - added `--exclude-url-host` so stale or low-quality intermediary hosts such as `news.google.com` can be excluded from candidate discovery.
  - local runtime RSS config was moved away from enabled Google News feeds toward direct official/publisher feeds under `/private/tmp/stockanalysis-runtime/news-rss-feeds.json`; the prior Google config was backed up outside the repo.
  - live DB raw fetch run_id 111 fetched 12 direct RSS article bodies from NVIDIA/Fed/SEC documents with 0 failures.
  - task contract/review and verification plan were updated.
- 진행 중:
  - none for this task.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: direct publisher raw artifacts are now available; continue with article boilerplate cleanup and deduplication so repeated NVIDIA Newsroom/Blog mirrors do not dominate the first page.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_fetch tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_fetch_cli_prints_summary -v`: 10 tests passed before host exclusion.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_raw_fetch tests.test_news_rss_raw_body_chunk_index tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_fetch_cli_prints_summary tests.test_ingest_cli.IngestCliTests.test_news_rss_raw_body_chunk_index_cli_prints_summary -v`: 22 tests passed after host exclusion.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_news_rss_raw_body_fetch.sh`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-rss-raw-body-fetch`: passed readiness checks.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_cli -v`: 47 tests passed.
- `git diff --check`: passed.
- Live CLI smoke run_id 99: requested 2, succeeded 2, failed 0, artifacts stored under `/private/tmp/stockanalysis-runtime/news-rss-raw`, no paid provider API, no live LLM.
- Live CLI smoke run_id 100: requested 1, succeeded 1, failed 0, artifact filename kept `.html` extension after the naming fix.
- Live CLI run_id 111: `--exclude-url-host news.google.com`, requested 12, succeeded 12, failed 0, stored direct NVIDIA/Fed/SEC raw artifacts, no paid provider API, no live LLM.

## Risks

- Public publishers can block automated article fetches or return consent/redirect pages.
- This task stores raw HTML only; raw HTML still includes page boilerplate and requires a cleaner article extractor before recommendation-quality evidence.
- URL validation blocks obvious local/private IP literal targets but does not perform DNS resolution based private-network blocking.
- Older Google News intermediary documents still exist in the local DB, but the new host exclusion prevents future raw-fetch/chunk-index batches from selecting them by default when `--exclude-url-host news.google.com` is used.
