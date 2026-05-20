# Task Contract

## Task

- 이름: recommendation-thesis-evidence-gates
- 요청: 추천과 투자 논리가 어떤 증거에 의해 뒷받침되는지, 어디가 비어 있는지 화면에서 점검 가능하게 만든다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - 추천 상세 API는 `evidence_review`를 포함한다.
  - 투자 논리 상세 API는 `evidence_review`를 포함한다.
  - 추천/투자 논리 화면은 근거 품질 점검, 통과/주의/차단 게이트, 다음 조치를 한국어로 보여준다.
  - 이 작업은 read-only이며 추천 점수, thesis 생성, benchmark, DB schema, broker/order, scheduler를 바꾸지 않는다.

## Scope

- 포함:
  - frontend live adapter DTO post-processing
  - recommendation/thesis evidence gate payloads
  - TypeScript contract update
  - recommendation and thesis page UI panels
  - targeted tests and browser check
- 제외:
  - 실제 추천 생성/리밸런싱
  - live LLM/RAG 호출
  - benchmark/evaluation split 변경
  - DB migration
  - paper/live order write flow
  - scheduler host activation

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `docs/plans/2026-05-20-recommendation-thesis-evidence-gates.md`
  - `docs/tasks/recommendation-thesis-evidence-gates/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-thesis-evidence-gates`
  - `git diff --check`

## Done Criteria

- [x] Recommendation detail API returns evidence gates.
- [x] Thesis detail API returns evidence gates.
- [x] Recommendation and thesis pages render the quality check in Korean.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
