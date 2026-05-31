# data-health-operator-cockpit-ux-v3 Handoff

## Status

- in_progress: `/data-health` 화면을 운영 로그가 아니라 수집·분석·추천 준비 상태 관제 화면으로 정리했고 EC2 smoke 전이다.

## Completed

- completed: task contract를 생성했다.
- completed: `페이퍼`, `가중치`, `주문 경계`, `벤치마크 drift`, `커버리지`, `runner` 계열의 주요 사용자 노출 문구를 `가상 매매`, `추천 산식 반영 비중`, `실거래 상태`, `벤치마크 괴리`, `연결률`, `실행 작업` 중심으로 정리했다.
- completed: 실행 기록 ID는 필요한 곳에서 `기록 있음/없음` 또는 `실행 #` 형태로 낮춰 표시하게 했다.

## Boundaries

- DB/API, scheduler, AI batch, alert destination, auth/RBAC, recommendation scoring, broker/order flow는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-operator-cockpit-ux-v3`
- passed: `git diff --check`
- pending: EC2 deploy and route/content smoke.
- pending: Playwright snapshot.

## Exact Next Step

- exact next step: 변경분을 커밋·푸시하고 EC2 배포, route/content smoke, Playwright snapshot을 수행한다.
