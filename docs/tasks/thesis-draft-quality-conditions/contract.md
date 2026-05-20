# Task Contract

## Task

- 이름: thesis-draft-quality-conditions
- 요청: 추천에서 생성되는 투자 논리 초안의 summary, 진입/유지 조건, 무효화 조건, exit 조건을 더 구체적으로 만든다.
- 담당: Codex
- 날짜: 2026-05-20

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - thesis title identity는 기존 검증과 호환되도록 유지된다.
  - thesis summary는 추천 점수, 사이클 상태/점수, 가격 feature, benchmark, 보유 기간을 포함한다.
  - entry/invalidation/exit 조건은 generic 문장보다 더 명확한 검토 기준을 제공한다.
  - invalidation 조건은 기존 검증 호환을 위해 `recommendation score falls below 0.3500` 문구를 유지한다.
  - 추천 점수 산식, DB schema, benchmark calculation, LLM 호출, provider 호출, broker/order, scheduler behavior는 바꾸지 않는다.

## Scope

- 포함:
  - deterministic thesis text generation helper
  - thesis bootstrap unit tests
  - local live thesis bootstrap rerun
  - live API/browser smoke
- 제외:
  - scoring formula changes
  - DB migration
  - thesis review action rule changes
  - AI/RAG generation
  - real provider calls
  - paper/live order write flow
  - scheduler host activation

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/signal/thesis.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_thesis_bootstrap.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/thesis-bootstrap.md`
  - `docs/plans/2026-05-20-thesis-draft-quality-conditions.md`
  - `docs/tasks/thesis-draft-quality-conditions/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_thesis_bootstrap -v`
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
  - local live `thesis-bootstrap` against repo-outside data operations env
  - live API smoke for `/api/theses/AAPL-bootstrap-v1`
  - browser smoke for `/theses/AAPL-bootstrap-v1`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task thesis-draft-quality-conditions`
  - `git diff --check`

## Done Criteria

- [x] Thesis bootstrap keeps the same title identity and linking behavior.
- [x] Thesis summary includes score, cycle, market feature, benchmark, and holding-period context.
- [x] Entry/invalidation/exit conditions are specific and deterministic.
- [x] Missing feature cases are represented explicitly.
- [x] Local live thesis detail reads the updated text.
- [x] Verification commands pass.
- [x] Handoff and review are updated.
