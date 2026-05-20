# Task Contract

## Task

- 이름: free-news-rss-event-enrichment
- 요청: 무료 RSS 뉴스 이벤트를 유료 API 없이 1차 종목/테마/영향 분류에 연결한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `news_rss_item` 이벤트가 `event_classification_impact`를 통해 내부 뉴스 테마에 연결될 수 있다.
  - 제목/요약에 명확한 종목 또는 지수 ETF 단서가 있으면 `event_instrument_impact`에 연결된다.
  - 모든 분류는 로컬 규칙 기반이며 외부 유료 API나 LLM 호출을 하지 않는다.
  - 기존 read-only frontend DTO/API 경계를 유지한다.

## Scope

- RSS 뉴스용 pending event enrichment 후보 조회 SQL을 추가한다.
- RSS feed name/키워드 기반 테마 매핑과 제목/요약 기반 종목 매핑을 추가한다.
- operations CLI에 단발 실행 커맨드를 추가한다.
- 관련 단위 테스트와 handoff를 남긴다.

## Boundaries

- DB schema, scoring, benchmark, recommendation logic, broker/order flow는 변경하지 않는다.
- 실제 투자 추천을 생성하지 않는다.
- 무료 RSS 원문 외 추가 provider 호출을 하지 않는다.
- 분류 실패는 이벤트 저장 실패가 아니라 enrichment 미완료 상태로 취급한다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ingest/news/*`
  - `src/stockanalysis/operations/cli.py`
  - `tests/test_news_rss_enrichment.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/free-news-rss-event-enrichment/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_news_rss_enrichment tests.test_data_operations_cli`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src/stockanalysis/ingest/news src/stockanalysis/operations/cli.py tests/test_news_rss_enrichment.py`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task free-news-rss-event-enrichment`
  - `git diff --check`

## Done Criteria

- [x] RSS enrichment command exists and is callable through backend operations CLI.
- [x] 테마 bootstrap/upsert가 RSS 뉴스 테마를 만든다.
- [x] 명확한 RSS 뉴스 후보가 종목/테마 impact로 연결된다.
- [x] 유료 API/LLM 호출이 없다.
- [x] required verification passes.
