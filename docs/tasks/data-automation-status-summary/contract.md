# Task Contract

## Task

- 이름: data-automation-status-summary
- 요청: 주식 캔들 수집, 뉴스 수집, AI 분석이 자동으로 되는지 사람이 한눈에 판단할 수 있게 `/data-health`에 요약한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/data-health`가 market-price-daily, news-rss-daily, event-intelligence-weekly 상태를 별도 운영 카드로 보여준다.
  - 화면은 최근 실행 상태와 반복 자동화/scheduler 활성화 상태를 분리해서 보여준다.
  - scheduler host activation, backend DTO, DB schema, provider/env, scoring, trading/order behavior는 변경하지 않는다.

## Scope

- 포함:
  - `apps/web/src/app/data-health/page.tsx`
  - docs plan/task
- 제외:
  - backend API/DTO changes
  - DB migration
  - real scheduler activation
  - env/secrets/feed/provider changes
  - live LLM/RAG calls
  - recommendation/thesis scoring changes
  - paper/live order writes

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/data-health/page.tsx`
  - `docs/plans/2026-05-20-data-automation-status-summary.md`
  - `docs/tasks/data-automation-status-summary/*`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - browser smoke for `/data-health`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task data-automation-status-summary`
  - `git diff --check`

## Done Criteria

- [x] Data-health shows candle/news/AI automation summary cards.
- [x] Summary separates recent successful runs from actual scheduler activation.
- [x] Browser smoke confirms the section is visible.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
