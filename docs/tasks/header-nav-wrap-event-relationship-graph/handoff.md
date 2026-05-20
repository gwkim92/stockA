# Session Handoff

## Active Task

- 이름: header-nav-wrap-event-relationship-graph
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract created.
  - header nav wraps onto additional rows instead of hiding overflow behind horizontal scrolling.
  - event list read model now returns `related_events` candidates derived from same source document, symbol, and theme.
  - `/events` renders related-event chips under each event with Korean labels.
  - `/intelligence` renders a relationship evidence panel and tolerates older live payloads without `related_events`.
  - FastAPI frontend API was restarted on `127.0.0.1:8787` so local Next routes read the new live payload shape.
- 진행 중:
  - none.
- 막힌 점:
  - none.

## Exact Next Step

- 다음 세션은 이것부터 시작: implement a free RSS/news source ingestion spike that writes source_document/event rows into the existing event pipeline, without changing scoring or broker execution.

## Verification

- Passed:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_api_adapter tests.test_frontend_live_adapter`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `curl -fsS -o /private/tmp/stockanalysis-runtime/intelligence.html -w '%{http_code}' http://127.0.0.1:3001/intelligence` returned `200`.
  - `curl -fsS -o /private/tmp/stockanalysis-runtime/events.html -w '%{http_code}' http://127.0.0.1:3001/events` returned `200`.
  - HTML smoke found relationship labels and found no `TypeError`, client-rendering fallback, or `Cannot read properties` text.
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task header-nav-wrap-event-relationship-graph`
  - `git diff --check`
  - Browser check on `http://127.0.0.1:3001/events` and `http://127.0.0.1:3001/intelligence`: nav has 15 links, wraps to two rows, no horizontal document overflow, and relationship graph text is rendered.

## Risks

- This is a read-model/UI slice.
- It does not add live general-news ingestion yet.
- It does not mutate recommendations or trading state.
