# Task Contract

## Task

- 이름: news-operation-flow-disclosure
- 요청: 뉴스 수집/분석/활용/자동화 흐름을 화면과 보고에서 사람이 이해할 수 있게 정리한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/intelligence` 화면에서 뉴스 수집 주기와 실행 상태가 보인다.
  - `/intelligence` 화면에서 뉴스가 RSS 수집, 이벤트 저장, 규칙 기반 enrichment, chunk/index, AI evidence cluster로 이어지는 흐름이 보인다.
  - 화면은 뉴스가 추천/투자 논리/종목/이벤트 화면에 어떻게 쓰이는지 설명한다.
  - scheduler host activation, DB schema, scoring, LLM/provider 호출, trading/order behavior는 변경하지 않는다.

## Scope

- 포함:
  - `apps/web/src/app/intelligence/page.tsx`
  - docs plan/task
- 제외:
  - backend DTO shape changes
  - DB migration
  - feed URL/secrets 변경
  - scheduler host activation
  - live LLM/RAG call
  - recommendation/thesis scoring changes
  - paper/live order writes

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/intelligence/page.tsx`
  - `docs/plans/2026-05-20-news-operation-flow-disclosure.md`
  - `docs/tasks/news-operation-flow-disclosure/*`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - browser smoke for `/intelligence`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task news-operation-flow-disclosure`
  - `git diff --check`

## Done Criteria

- [x] News operation flow is visible on `/intelligence`.
- [x] The flow explains cadence, collection, enrichment, AI evidence, project usage, and automation status.
- [x] Browser smoke confirms the new section is visible.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
