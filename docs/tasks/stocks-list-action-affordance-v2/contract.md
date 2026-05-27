# stocks-list-action-affordance-v2 Contract

## Task Request

- request: 종목 목록 화면에서 개별 종목 상세 진입과 추천 근거 진입이 분명히 보이게 하고, 행 전체가 클릭되는 것처럼 느껴지는 혼란을 줄인다.

## Goal

- goal: `/stocks`에서 사용자가 추천·보유 연결이 있는 종목을 먼저 보고, 각 행의 명확한 버튼으로 종목 상세와 추천 근거 화면으로 이동할 수 있다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/stocks/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/stocks-list-action-affordance-v2/*`

## Invariants

- 추천 scoring formula, recommendation weights, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- 새 API, DB schema, scheduler, AI 호출을 추가하지 않는다.
- 이 작업은 UX affordance와 한국어 문구 정리만 수행한다.

## Scope

- `/stocks` hero 문구를 종목 상세 진입 목적에 맞게 정리한다.
- 추천·보유 연결이 있는 우선 확인 종목 카드와 CTA를 추가한다.
- 목록 테이블에 `상세 확인` 열을 추가하고 `종목 상세 보기`, `추천 근거 보기` 버튼을 명시한다.
- 행 전체가 링크가 아니라 종목명과 버튼만 이동 대상임을 문구와 UI로 표시한다.
- 모바일에서 액션 버튼이 줄바꿈 없이 명확히 보이도록 CSS를 보정한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stocks-list-action-affordance-v2`
- verification command: `git diff --check`
- verification command: EC2/local tunnel route smoke for `/stocks`

## Done Criteria

- [x] `/stocks`에 “오늘 먼저 볼 종목” 섹션이 렌더링된다.
- [x] 목록 행에 명확한 `종목 상세 보기` 버튼이 렌더링된다.
- [x] 추천이 있는 종목은 `추천 근거 보기` 버튼이 렌더링된다.
- [x] 행 전체가 링크가 아니라는 안내 문구가 보인다.
- [x] local verification과 EC2 route smoke가 통과한다.
