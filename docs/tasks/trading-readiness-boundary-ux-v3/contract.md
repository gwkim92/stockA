# trading-readiness-boundary-ux-v3

## Task Request

- request: `/trading-readiness` 화면을 실제 주문 가능 화면처럼 보이지 않게 정리하고, 실거래 차단·가상 매매 검증·검토 기록을 명확히 보여준다.

## Goal

- goal: 사용자가 `실거래는 차단`, `가상 매매 검증은 검토 근거`, `증권사 제출 기능은 꺼짐/켜짐`, `킬 스위치와 주문 한도는 별도 안전장치`를 바로 이해한다.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/trading-readiness/page.tsx`
  - `docs/tasks/trading-readiness-boundary-ux-v3/*`

## Non-Goals

- broker/order flow, 계좌 권한, 주문 한도, kill switch, paper validation 계산, DB/API DTO는 변경하지 않는다.
- 실거래 주문 버튼, 쓰기 API, 승인 버튼을 추가하지 않는다.

## Acceptance Criteria

- `/trading-readiness` 상단에서 실제 주문 전송 건수, 실거래 차단 여부, 증권사 제출 기능, 가상 매매 검증 상태가 바로 보인다.
- `페이퍼`, `주문 경계`, raw broker/order code 같은 표현이 주요 사용자 문구로 노출되지 않는다.
- 가상 매매 검증과 실제 주문 제출이 명확히 분리되어 보인다.
- Next.js typecheck/build, AWH verify, diff check를 통과한다.
- EC2 route/content smoke와 Playwright snapshot으로 핵심 문구를 확인한다.

## Verification

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task trading-readiness-boundary-ux-v3`
- verification command: `git diff --check`
- verification command: EC2 route/content smoke for `/trading-readiness`
- verification command: Playwright snapshot for `http://127.0.0.1:13000/trading-readiness`

## Boundaries

- 이번 작업은 UX/copy visibility slice다.
- 실거래 차단 상태와 안전 경계는 낮춰 보이지 않게 유지한다.
