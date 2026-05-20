# Session Handoff

## Active Task

- 이름: frontend-current-news-events
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract created.
  - `getEvents()` now defaults to the current ISO date and keeps `eventType`/`limit` explicit.
  - `/events` Korean copy now explains the live news/evidence ledger instead of the old English fixture wording.
  - `/events` renders latest RSS/news rows from the live API on the current date.
  - Event status codes visible to users now render as Korean labels: `뉴스 RSS 항목`, `종목 미분류`, `테마 미분류`, `원천 문서 검토 필요`.
- 진행 중:
  - none.
- 막힌 점:
  - none.

## Exact Next Step

- 다음 세션은 이것부터 시작: add RSS event classification/enrichment so `news_rss_item` rows are linked to symbols/themes and impact evidence instead of staying `종목 미분류`/`테마 미분류`.

## Verification

- Passed:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `curl -fsS -o /private/tmp/stockanalysis-runtime/events-current.html -w '%{http_code}' http://127.0.0.1:3001/events` returned `200`.
  - `rg "종목 미분류|테마 미분류|뉴스 RSS 항목|원천 문서 검토 필요|오늘 수집된 뉴스" /private/tmp/stockanalysis-runtime/events-current.html` found current RSS/news screen content.
  - `rg "UNKNOWN|UNCLASSIFIED|news rss item|source document review required" /private/tmp/stockanalysis-runtime/events-current.html` returned no matches.
  - Browser check for `http://127.0.0.1:3001/events`: Korean labels present; raw code labels absent; first rows show real RSS headlines.
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-current-news-events`
  - `git diff --check`

## Risks

- This only changes read/display defaults. RSS event classification, AI extraction, and recommendation impact remain future work.
