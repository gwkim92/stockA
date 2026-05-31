# performance-outcome-ux-v3

## Task Request

- request: `/performance` 화면을 성과 로그가 아니라 중장기 추천의 책임 추적 화면으로 정리한다.

## Goal

- goal: 사용자가 `성과 측정 가능 여부`, `표본 품질`, `성과 귀속`, `제외/보완 항목`, `추천 산식 변경 금지`를 한눈에 이해한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/performance/page.tsx`
  - `docs/tasks/performance-outcome-ux-v3/*`

## Non-Goals

- 성과 계산, attribution 계산, benchmark, recommendation scoring, outcome maturity policy, DB/API DTO는 변경하지 않는다.
- 추천 산식 반영 비중 또는 실거래 경계를 바꾸지 않는다.

## Acceptance Criteria

- `/performance` 상단에서 성과가 측정됐는지, 아직 측정 전인지, 표본을 믿어도 되는지 바로 보인다.
- `커버리지`, `가중치`, `페이퍼 검증`, raw source/run 용어가 주요 사용자 문구로 노출되지 않는다.
- 성과 해석은 자동 추천 산식 변경이나 주문 근거가 아니라는 경계가 명확하다.
- Next.js typecheck/build, AWH verify, diff check를 통과한다.
- EC2 route/content smoke와 Playwright snapshot으로 핵심 문구를 확인한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task performance-outcome-ux-v3`
- verification command: `git diff --check`
- verification command: EC2 route/content smoke for `/performance`
- verification command: Playwright snapshot for `http://127.0.0.1:13000/performance`

## Boundaries

- 이번 작업은 UX/copy visibility slice다.
- 성과가 좋아 보이더라도 outcome maturity gate 전까지 추천 산식 변경을 허용하지 않는다.
