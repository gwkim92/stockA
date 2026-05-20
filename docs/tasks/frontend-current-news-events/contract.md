# Task Contract

## Task

- 이름: frontend-current-news-events
- 요청: 실제 수집된 무료 RSS/news 이벤트가 `/events` 화면 기본 조회에 보이도록 한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/events` 기본 조회가 2024 fixture 날짜가 아니라 현재 날짜 기준 live 이벤트를 읽는다.
  - 최신 `news_rss_item` 이벤트가 화면에 표시될 수 있다.
  - 기존 read-only DTO/API 경계를 유지한다.

## Scope

- `apps/web/src/lib/frontend-api.ts`의 `getEvents`를 parameterized current-date default로 바꾼다.
- `/events` 페이지 문구를 최신 뉴스/공시 이벤트 입력을 설명하도록 보정한다.
- 화면에 보이는 이벤트 상태 코드를 한국어 운영 라벨로 표시한다.
- typecheck/build/route smoke를 검증한다.

## Boundaries

- DB schema, scoring, benchmark, recommendation, broker/order flow는 변경하지 않는다.
- 새 write endpoint를 만들지 않는다.
- feed URL이나 token을 프론트에 노출하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/app/events/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/frontend-current-news-events/*`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `curl -fsS -o /private/tmp/stockanalysis-runtime/events-current.html -w '%{http_code}' http://127.0.0.1:3001/events`
  - `rg "news_rss_item|뉴스 RSS 항목|원천 문서" /private/tmp/stockanalysis-runtime/events-current.html`
  - Browser check for `/events` visible text: Korean labels present, raw `UNKNOWN`/`UNCLASSIFIED`/`news rss item`/`source document review required` absent.
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-current-news-events`
  - `git diff --check`

## Done Criteria

- [x] event page reads current-date live event list by default.
- [x] page wording explains news/evidence ledger clearly.
- [x] latest RSS/news event appears in route smoke.
- [x] required verification passes.
