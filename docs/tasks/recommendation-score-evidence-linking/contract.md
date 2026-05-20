# Task Contract

## Task

- 이름: recommendation-score-evidence-linking
- 요청: 추천 점수 구성요소를 실제 이벤트/AI 근거 ID에 연결하여 추천 근거 품질 점검이 통과 가능하게 만든다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 추천 상세 SQL은 추천 종목의 최신 원천 이벤트/AI artifact를 read-only anchor로 찾는다.
  - 점수 구성요소 중 cycle/event-like component는 가능한 경우 `ai-evidence-*` 또는 `event-*` 근거 ID를 갖는다.
  - 추천 상세 화면에서 concrete evidence id는 유효한 화면으로 이동한다.
  - 추천 점수, DB schema, benchmark, LLM 호출, broker/order, scheduler behavior는 바꾸지 않는다.

## Scope

- 포함:
  - recommendation detail SQL read-only evidence anchor
  - recommendation links and frontend evidence link rendering
  - targeted tests
  - live API and browser smoke
- 제외:
  - scoring formula changes
  - recommendation generation
  - thesis generation
  - DB migration
  - live LLM/RAG call
  - paper/live order write flow
  - scheduler host activation

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/plans/2026-05-20-recommendation-score-evidence-linking.md`
  - `docs/tasks/recommendation-score-evidence-linking/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-score-evidence-linking`
  - `git diff --check`

## Done Criteria

- [x] Recommendation detail SQL includes event/AI evidence anchor CTEs.
- [x] Recommendation detail API returns concrete evidence-linked score components in tested fixture/live paths.
- [x] Recommendation page links concrete evidence ids to valid routes.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
