# Task Contract

## Task

- 이름: free-news-rss-config-runner
- 요청: 무료 RSS/news feed 목록을 repo 밖 설정 파일로 관리하고 여러 feed를 실행하는 runner를 추가한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 무료 RSS/Atom feed 목록은 repo 밖 JSON config에서 읽는다.
  - `stockanalysis-operations`가 여러 feed를 `news-rss-upsert` 경계로 순차 실행할 수 있다.
  - config report는 feed 이름, 활성 여부, host, limit만 노출하고 full URL/token 값은 출력하지 않는다.
  - env readiness가 repo 밖 feed config 존재와 형식을 검증한다.

## Scope

- `news_rss_feed_config` env group과 template 추가.
- repo-outside feed config loader/validator/report 추가.
- `stockanalysis-operations news-rss-config-report` 추가.
- `stockanalysis-operations news-rss-daily-run` 추가.
- runner/unit/CLI/env readiness tests 추가.

## Boundaries

- 유료 provider, API key, 크롤링 우회, scraping bypass는 추가하지 않는다.
- 실제 publisher feed URL은 repo에 커밋하지 않는다.
- DB schema, scoring, benchmark, evaluation split은 바꾸지 않는다.
- AI RAG/ontology, 추천 판단, broker/order flow는 변경하지 않는다.
- report에는 full feed URL이나 secret 값을 출력하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/env_readiness.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/news_rss_feed_runner.py`
  - `tests/test_news_rss_feed_runner.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_env_readiness.py`
  - `tests/test_data_operations_cadence.py`
  - `docs/plans/2026-05-19-free-news-rss-config-runner.md`
  - `docs/tasks/free-news-rss-config-runner/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_feed_runner tests.test_data_operations_cli tests.test_data_operations_env_readiness tests.test_data_operations_cadence`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src/stockanalysis/operations src/stockanalysis/ingest/news`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task free-news-rss-config-runner`
  - `git diff --check`

## Done Criteria

- [x] repo-outside feed config validates version, feed names, http(s) URLs, enabled state, and limits.
- [x] config report is URL-redacted and safe to expose in data operations UI/logs.
- [x] daily runner can execute multiple enabled feeds through `news-rss-upsert`.
- [x] env readiness includes `news_rss_feed_config`.
- [x] required verification passes.
