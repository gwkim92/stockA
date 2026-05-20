# Task Contract

## Task

- 이름: thesis-review-quality-rationale
- 요청: thesis review가 왜 watch/reduce/exit/keep인지 사람이 이해할 수 있는 rationale을 저장한다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - thesis review action rule은 기존과 호환된다.
  - review summary는 추천 점수, 추천 action/bucket, 사이클 상태/점수, 가격 feature, 다음 검토일을 포함한다.
  - change notes는 action을 유발한 deterministic signal을 나열한다.
  - missing cycle/price feature는 명시적으로 표시된다.
  - 추천 점수 산식, DB schema, benchmark calculation, LLM 호출, provider 호출, broker/order, scheduler behavior는 바꾸지 않는다.

## Scope

- 포함:
  - deterministic thesis review rationale helper
  - thesis review bootstrap unit tests
  - local live thesis-review bootstrap rerun
  - live API/browser smoke
  - docs update
- 제외:
  - thesis review action rule changes
  - scoring formula changes
  - DB migration
  - AI/RAG review generation
  - real provider calls
  - paper/live order write flow
  - scheduler host activation

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/signal/thesis_review.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_thesis_review_bootstrap.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/theses/[thesisId]/page.tsx`
  - `docs/thesis-review-bootstrap.md`
  - `docs/plans/2026-05-20-thesis-review-quality-rationale.md`
  - `docs/tasks/thesis-review-quality-rationale/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_thesis_review_bootstrap -v`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
  - local live `thesis-review-bootstrap` against repo-outside data operations env
  - live API smoke for `/api/theses/AAPL-bootstrap-v1`
  - browser smoke for `/theses/AAPL-bootstrap-v1`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task thesis-review-quality-rationale`
  - `git diff --check`

## Done Criteria

- [x] Thesis review action behavior remains compatible.
- [x] Review summary/change notes explain action rationale in Korean.
- [x] Missing cycle/price feature cases are represented explicitly.
- [x] Local live thesis detail reads the updated review state.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
