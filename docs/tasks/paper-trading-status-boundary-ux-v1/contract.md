# paper-trading-status-boundary-ux-v1

## Task Request

- request: 전체 UX/UI 리팩터링 흐름에서 `/paper-trading` 화면을 이어서 정리한다.

## Goal

- goal: 페이퍼 거래 화면에서 실제 주문, 가상 검증 후보, 차단 조건, 다음 확인 위치를 사용자가 바로 구분하게 만든다.

핵심 질문은 아래 네 가지다.

- 실제 증권사 주문이 나갔는가?
- 화면에 보이는 항목은 주문 지시인가, 가상 검증 후보인가?
- 어떤 안전 조건 때문에 실거래로 넘어갈 수 없는가?
- 후보별 추천서, 투자 논리, 종목 상세 중 무엇을 이어서 봐야 하는가?

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `docs/tasks/paper-trading-status-boundary-ux-v1/*`

## Non-Goals

- 실제 broker/order submit 활성화 금지
- paper validation 계산 로직 변경 금지
- 추천 score component weight 변경 금지
- benchmark, portfolio position, outcome record 변경 금지
- DB schema, API DTO, scheduler cadence 변경 금지

## Acceptance Criteria

- `/paper-trading` 첫 화면에서 `실제 주문 0건`, `가상 검증 후보`, `차단 조건`, `다음 확인`이 분리되어 보인다.
- 사용자 화면의 `broker flow`, `human approval`, `paper validation`, `weight`, `thesis` 같은 내부/혼합 표현이 필요한 곳을 제외하고 한국어 사용자 문장으로 바뀐다.
- 가상 후보 표가 주문 지시처럼 보이지 않고, 추천서·투자 논리·종목 상세로 이어지는 검토 경로를 보여준다.
- 검증은 Next typecheck/build, AWH task verify, EC2 route smoke로 확인한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task paper-trading-status-boundary-ux-v1`
- verification command: EC2 route/content smoke for `/paper-trading`
