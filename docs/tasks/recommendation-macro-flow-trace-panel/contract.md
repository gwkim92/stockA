# Task Contract

## Task

- 이름: recommendation-macro-flow-trace-panel
- 요청: 추천 상세에서 상위 흐름 후보가 추천 점수로 들어간 경로를 눈에 보이게 표시한다.
- 담당: Codex
- 날짜: 2026-05-22

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/recommendations/[id]`가 `macro_flow_score` provenance의 `recent_flows`를 별도 패널로 보여준다.
  - 사용자는 추천 점수에 들어간 상위 흐름의 테마, 방향, 강도, 신뢰도, 원천 이벤트 제목을 볼 수 있다.
  - 데이터가 없을 때는 패널을 숨겨 기존 추천 상세를 방해하지 않는다.

## Scope

- 포함:
  - recommendation detail page UI 보강
  - frontend type/build/browser smoke
  - task handoff와 검증 기록
- 제외:
  - DB migration
  - API contract 변경
  - recommendation scoring 변경
  - scheduler cadence 변경
  - broker/order flow

## Mutable Surface

- 수정 가능한 파일:
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `docs/tasks/recommendation-macro-flow-trace-panel/*`
- 수정 금지 파일:
  - `.env` secret values
  - DB migrations/schema
  - scheduler units/timers
  - recommendation scoring weights
  - broker/order submission code

## Verification Commands

- 검증에 사용할 명령:
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-macro-flow-trace-panel`
  - Browser smoke for a recommendation detail route

## Done Criteria

- [x] Macro flow components are detected from existing provenance data.
- [x] Recent propagated flow rows are displayed with title/theme/direction/strength/confidence.
- [x] No API/schema/scoring change is required.
- [x] Local verification and AWH pass.
- [ ] EC2 deploy and browser smoke pass.
