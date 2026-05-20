# Task Contract

## Task

- 이름: performance-quality-evaluation-summary
- 요청: 추천/투자 논리 품질이 실제 성과와 정렬되는지 `/performance`에서 사람이 판단할 수 있게 만든다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/performance/{portfolio}/outcomes` 응답에 `quality_evaluation` 객체가 포함된다.
  - `quality_evaluation`은 표본 수, 점수-성과 정렬, review-outcome 불일치, 커버리지 상태를 포함한다.
  - `/performance` 화면은 해당 내용을 한국어로 표시한다.
  - 추천 산식, DB schema, benchmark, evaluation split, paper/live order behavior는 변경하지 않는다.

## Scope

- 포함:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/performance/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - docs plan/task
- 제외:
  - DB migration
  - recommendation/thesis scoring formula changes
  - recommendation/thesis generation changes
  - live LLM/RAG calls
  - scheduler host activation
  - paper/live order writes

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/performance/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `docs/plans/2026-05-20-performance-quality-evaluation-summary.md`
  - `docs/tasks/performance-quality-evaluation-summary/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - browser smoke for `/performance`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task performance-quality-evaluation-summary`
  - `git diff --check`

## Done Criteria

- [x] Performance API includes `quality_evaluation`.
- [x] Performance page shows recommendation quality evaluation in Korean.
- [x] Performance attribution and quality gate wording avoid raw English backend strings.
- [x] Browser smoke confirms the section is visible.
- [x] Final verification commands pass.
- [x] Handoff and review are updated.
