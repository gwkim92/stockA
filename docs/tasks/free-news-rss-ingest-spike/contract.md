# Task Contract

## Task

- 이름: free-news-rss-ingest-spike
- 요청: 무료 RSS/news feed를 수집해 기존 source_document/event 파이프라인에 적재하는 첫 slice를 구현한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - API key 없는 RSS/Atom feed 또는 local XML fixture를 읽을 수 있다.
  - feed item은 `ingest.source_document`에 upsert된다.
  - feed item별 기본 `event.event`와 `event.event_document_link`가 생성된다.
  - 기존 recommendation scoring, benchmark, evaluation split, broker/order flow는 변경하지 않는다.

## Scope

- `rss_news` ingest source adapter 추가.
- RSS/Atom parser와 deterministic external document id/checksum 생성.
- `news-rss-upsert` CLI 추가.
- source document/event upsert SQL 추가.
- unit/CLI/registry tests 추가.
- data operations cadence에 `news_rss_upsert` expected job 추가.
- task handoff와 계획 문서 갱신.

## Boundaries

- 외부 유료 provider, API key, scraping 우회는 추가하지 않는다.
- DB schema는 바꾸지 않는다.
- AI 요약/분류/RAG/ontology 런타임은 이번 slice에서 만들지 않는다.
- 추천 점수, thesis, portfolio, paper/live trading 상태는 변경하지 않는다.
- secrets, token, DB URL을 출력하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/ingest/registry.py`
  - `src/stockanalysis/ingest/sources/rss_news.py`
  - `src/stockanalysis/ingest/news/*`
  - `tests/test_ingest_sources.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_news_rss.py`
  - `src/stockanalysis/operations/cadence.py`
  - `tests/test_data_operations_cadence.py`
  - `tests/fixtures/news_rss_*.xml`
  - `docs/plans/2026-05-19-free-news-rss-ingest-spike.md`
  - `docs/tasks/free-news-rss-ingest-spike/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ingest_sources tests.test_ingest_cli tests.test_news_rss`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_data_operations_cadence`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m stockanalysis.ingest.cli news-rss-sync --feed-name fixture --feed-xml tests/fixtures/news_rss_sample.xml --feed-url https://example.com/rss --limit 2`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task free-news-rss-ingest-spike`
  - `git diff --check`

## Done Criteria

- [x] RSS/Atom parser produces deterministic item records.
- [x] `rss_news` source adapter can build free feed requests without credentials.
- [x] `news-rss-upsert` records pipeline run, source documents, events, and document links.
- [x] CLI has a fixture sync path for no-network verification.
- [x] data-health expected jobs include the RSS news ingest pipeline.
- [x] required verification passes.
