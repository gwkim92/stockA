# trading-readiness-boundary-ux-v3 Handoff

## Status

- in_progress: `/trading-readiness` 화면을 실제 주문 차단과 가상 매매 검증 중심으로 정리했고 EC2 smoke 전이다.

## Completed

- completed: task contract를 생성했다.
- completed: `페이퍼`, `가상 거래`, `주문 경계` 계열의 주요 사용자 노출 문구를 `가상 매매`, `가상 매매 검증`, `실거래 상태`로 정리했다.
- completed: 가상 매매 검증과 실제 주문 제출 기능이 분리되어 보이도록 상단 카드와 세부 섹션 문구를 정리했다.

## Boundaries

- broker/order flow, 계좌 권한, 주문 한도, kill switch, paper validation 계산, DB/API DTO는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task trading-readiness-boundary-ux-v3`
- passed: `git diff --check`
- pending: EC2 deploy and route/content smoke.
- pending: Playwright snapshot.

## Exact Next Step

- exact next step: 변경분을 커밋·푸시하고 EC2 배포, route/content smoke, Playwright snapshot을 수행한다.
