# Task Contract

## Task

- 이름: frontend-news-cluster-analysis
- 요청: 무료 RSS 뉴스 이벤트가 어떤 테마/종목 묶음으로 연결되는지 `/intelligence`에서 사람이 이해할 수 있게 보여준다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/intelligence`가 최신 이벤트를 테마/종목 기준으로 묶어 보여준다.
  - 각 묶음은 발생한 뉴스 수, 연결 종목, 영향 방향, 대표 헤드라인, 연결 이유를 한국어로 설명한다.
  - 기존 read-only frontend DTO/API 경계를 유지한다.
  - 유료 API, LLM 호출, 자동 추천 생성은 추가하지 않는다.

## Scope

- `events.events`와 `related_events`만 사용해 프론트 서버 컴포넌트에서 로컬 집계를 만든다.
- `/intelligence` 화면에 “뉴스 묶음 분석” 섹션을 추가한다.
- 화면에 노출되는 코드형 값은 기존 한국어 라벨 경유로 표시한다.
- task handoff와 검증 증거를 남긴다.

## Boundaries

- DB schema, scoring, benchmark, recommendation logic, broker/order flow는 변경하지 않는다.
- AI evidence DB writer나 RAG/ontology 저장소는 이번 범위에 추가하지 않는다.
- 뉴스 묶음은 투자 결론이 아니라 검토용 read-only 요약으로만 표시한다.
- feed URL, token, DB URL 등 운영 시크릿은 화면과 문서에 노출하지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/intelligence/page.tsx`
  - `docs/tasks/frontend-news-cluster-analysis/*`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `curl -fsS -o /private/tmp/stockanalysis-runtime/intelligence-news-clusters.html -w '%{http_code}' http://127.0.0.1:3001/intelligence`
  - `rg "뉴스 묶음 분석|AI 반도체 사이클|금리·연준|같은 테마" /private/tmp/stockanalysis-runtime/intelligence-news-clusters.html`
  - Browser check for `/intelligence`: Korean cluster section visible; raw theme codes absent from visible text.
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task frontend-news-cluster-analysis`
  - `git diff --check`

## Done Criteria

- [x] news cluster cards render on `/intelligence`.
- [x] visible wording explains what happened, how it was analyzed, and why events are connected.
- [x] no paid provider or LLM call is added.
- [x] required verification passes.
