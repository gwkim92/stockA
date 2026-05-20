# Task Contract

## Task

- 이름: recommendation-thesis-quality-evaluation-view
- 요청: 추천/투자 논리가 실제 중장기 투자 검토 품질에 충분한지 화면에서 판단 가능하게 만든다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 추천 상세 화면에 read-only 중장기 품질 판정이 보인다.
  - 투자 논리 상세 화면에 read-only 중장기 품질 판정이 보인다.
  - 판정은 기존 score, outcome, evidence_review, latest_review만 사용하고 점수/DB/주문을 변경하지 않는다.
  - AI/RAG live call, scheduler activation, broker/order behavior는 변경하지 않는다.

## Scope

- 포함:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - docs plan/task
- 제외:
  - backend API/DTO changes
  - DB migration
  - scoring formula changes
  - recommendation/thesis generation changes
  - live LLM/RAG calls
  - scheduler host activation
  - paper/live order writes

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `docs/plans/2026-05-20-recommendation-thesis-quality-evaluation-view.md`
  - `docs/tasks/recommendation-thesis-quality-evaluation-view/*`

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - browser smoke for `/recommendations/AAPL-2024-11-01`
  - browser smoke for `/theses/AAPL-bootstrap-v1`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-thesis-quality-evaluation-view`
  - `git diff --check`

## Done Criteria

- [x] Recommendation detail shows long-term quality evaluation.
- [x] Thesis detail shows long-term quality evaluation.
- [x] Browser smoke confirms both panels are visible.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
