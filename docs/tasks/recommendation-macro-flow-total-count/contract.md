# Task Contract

## Task

- 이름: recommendation-macro-flow-total-count
- 요청: 추천 상세의 상위 흐름 전파 근거 총개수와 최근 preview 개수가 혼동되지 않게 한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/recommendations/[id]`의 `macro_flow_propagation.evidence.propagated_impact_count`는 전체 전파 row 수를 뜻한다.
  - `recent_flows`는 최근 preview rows로 제한된다.
  - `/recommendations/[id]`는 전체 개수와 preview 성격을 명확히 표시한다.

## Scope

- 포함:
  - recommendation detail SQL CTE 보강
  - focused regression test
  - recommendation detail UI copy 보강
  - task handoff와 검증 기록
- 제외:
  - DB migration
  - recommendation scoring 변경
  - scheduler cadence 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/tasks/recommendation-macro-flow-total-count/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler units/timers
  - recommendation scoring weights
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-macro-flow-total-count`
  - EC2 API/browser smoke for `/recommendations/recommendation-52`

## Done Criteria

- [x] Detail SQL separates all macro-flow rows from recent preview rows.
- [x] `propagated_impact_count` is not limited by preview row limit.
- [x] UI explains that visible rows are recent examples.
- [x] Local verification and AWH pass.
- [x] EC2 deploy and browser smoke pass.
