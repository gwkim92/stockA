# Task Contract

## Task

- 이름: recommendation-list-macro-flow-summary
- 요청: 추천 목록에서 상위 흐름 근거가 붙은 종목을 상세 진입 전에도 볼 수 있게 한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/recommendations` summary가 상위 흐름 근거가 있는 추천 수를 제공한다.
  - 각 recommendation row가 `macro_flow_component_count`, `macro_flow_evidence_count`를 제공한다.
  - `/recommendations` 화면에서 상위 흐름 근거 개수와 상세 진입 안내가 보인다.

## Scope

- 포함:
  - frontend live adapter recommendation list SQL/response contract 보강
  - Next.js recommendation list UI 보강
  - focused backend contract test
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
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/recommendations/page.tsx`
  - `docs/tasks/recommendation-list-macro-flow-summary/*`
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
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-list-macro-flow-summary`
  - EC2 API/browser smoke for `/recommendations`

## Done Criteria

- [x] API summary includes `macro_flow_evidence_recommendation_count`.
- [x] Recommendation row evidence includes `macro_flow_component_count` and `macro_flow_evidence_count`.
- [x] `/recommendations` shows macro-flow evidence count and links users to detail.
- [x] Local verification and AWH pass.
- [x] EC2 deploy and browser smoke pass.
