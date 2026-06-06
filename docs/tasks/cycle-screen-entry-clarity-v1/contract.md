# cycle-screen-entry-clarity-v1

## Request

- request: 사이클 화면 위치와 사이클 추적 여부가 화면과 API 계약에서 명확히 보이게 한다.
- 사용자가 사이클 화면 위치와 사이클 추적 여부를 바로 알 수 있게 한다.
- `/cycle-map` live endpoint가 화면과 adapter에는 있지만 frontend API contract index에 빠진 누락을 정리한다.

## Goal

- goal: `/cycles`는 테마별 사이클 상태표, `/cycle-map`은 거시→도메인→테마→종목 경로 지도라는 역할을 사용자가 첫 화면과 내비게이션에서 바로 이해하게 한다.

## Scope

- Mutable surface:
  - `apps/web/src/app/layout.tsx`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/cycle-map/page.tsx`
  - `docs/frontend-api-contract.md`
  - `docs/api/frontend/contract-index.json`
  - `docs/api/frontend/examples/cycle-map.json`
  - frontend API adapter/fixture contract tests
- Out of scope:
  - 추천 scoring weight 변경
  - portfolio position 변경
  - broker/order flow 변경
  - scheduler cadence 변경
  - cycle scoring formula 변경

## Acceptance

- 상단 내비게이션에서 사이클 화면을 직접 찾을 수 있다.
- 홈 화면에서 `/cycles`와 `/cycle-map`의 역할 차이가 보인다.
- `/cycle-map`이 frontend API contract index와 fixture endpoint list에 포함된다.
- EC2에서 `/cycles`, `/cycle-map`, `/api/cycles?asOfDate=<today>`, `/api/cycle-map?asOfDate=<today>`가 정상 응답한다.
- 사이클 추적 상태는 data-health의 `cycle_state_snapshot`, `cycle_community_ai_summary` 최신 성공으로 확인한다.

## Boundaries

- 이 작업은 visibility/contract alignment 작업이다.
- 사이클 계산식, 추천 산식, portfolio benchmark, 실거래 경계는 바꾸지 않는다.

## Verification Commands

- verification command: `npm run typecheck` in `apps/web`
- verification command: `npm run build` in `apps/web`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_api_adapter tests.test_frontend_fixture_server`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cycle-screen-entry-clarity-v1`
