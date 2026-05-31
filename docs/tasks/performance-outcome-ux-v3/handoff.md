# performance-outcome-ux-v3 Handoff

## Status

- in_progress: `/performance` 화면을 성과 측정, 표본 품질, 성과 귀속, 보완 항목 중심으로 정리했고 EC2 smoke 전이다.

## Completed

- completed: task contract를 생성했다.
- completed: `커버리지`, `가중치`, `페이퍼 검증` 계열의 주요 사용자 노출 문구를 `성과 연결 상태`, `추천 산식 반영 비중`, `가상 매매 검증`으로 정리했다.
- completed: 성과 해석이 자동 추천 산식 변경이나 주문 근거가 아니라는 경계를 상단과 품질 카드에 유지했다.

## Boundaries

- 성과 계산, attribution 계산, benchmark, recommendation scoring, outcome maturity policy, DB/API DTO는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task performance-outcome-ux-v3`
- passed: `git diff --check`
- pending: EC2 deploy and route/content smoke.
- pending: Playwright snapshot.

## Exact Next Step

- exact next step: 변경분을 커밋·푸시하고 EC2 배포, route/content smoke, Playwright snapshot을 수행한다.
