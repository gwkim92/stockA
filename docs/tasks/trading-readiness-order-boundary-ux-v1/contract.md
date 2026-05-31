# trading-readiness-order-boundary-ux-v1

## Task Request

- request: `/paper-trading` UX 정리 이후 연결 화면인 `/trading-readiness`를 이어서 정리한다.

## Goal

- goal: 거래 안전 화면에서 실제 주문 가능 여부가 아니라, 실제 주문을 막는 안전 경계와 차단 사유를 사용자가 바로 이해하게 만든다.

핵심 질문은 아래 네 가지다.

- 현재 서버에서 실제 주문이 전송됐는가?
- 증권사 주문 제출 기능은 켜져 있는가?
- 어떤 계좌 권한, 주문 한도, 킬 스위치, 위험 예산 조건이 막고 있는가?
- 페이퍼 검증 통과 후보가 있어도 왜 실제 주문이 아닌가?

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/trading-readiness/page.tsx`
  - `docs/tasks/trading-readiness-order-boundary-ux-v1/*`

## Non-Goals

- broker/order submit 활성화 금지
- paper validation 계산 로직 변경 금지
- 추천 score component weight 변경 금지
- benchmark, portfolio position, outcome record 변경 금지
- DB schema, API DTO, scheduler cadence 변경 금지

## Acceptance Criteria

- `/trading-readiness` 첫 화면에서 실제 주문 기록, 주문 제출 기능, 킬 스위치, 페이퍼 검증 경계가 분리되어 보인다.
- 사용자 화면의 `broker submit`, `broker boundary`, `scope`, `audit boundary`, `승인 후보` 같은 내부/혼합 표현이 한국어 사용자 문장으로 바뀐다.
- 리밸런싱 검토 후보와 위험 예산 사유가 주문 목표가 아니라 차단/검토 근거임을 명확히 표시한다.
- 검증은 Next typecheck/build, AWH task verify, EC2 route smoke로 확인한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task trading-readiness-order-boundary-ux-v1`
- verification command: EC2 route/content smoke for `/trading-readiness`
