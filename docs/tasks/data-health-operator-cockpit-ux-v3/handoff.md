# data-health-operator-cockpit-ux-v3 Handoff

## Status

- completed: `/data-health` 화면을 운영 로그가 아니라 수집·분석·추천 준비 상태 관제 화면으로 정리했고 EC2/Playwright smoke까지 확인했다.

## Completed

- completed: task contract를 생성했다.
- completed: `페이퍼`, `가중치`, `주문 경계`, `벤치마크 drift`, `커버리지`, `runner` 계열의 주요 사용자 노출 문구를 `가상 매매`, `추천 산식 반영 비중`, `실거래 상태`, `벤치마크 괴리`, `연결률`, `실행 작업` 중심으로 정리했다.
- completed: 실행 기록 ID는 필요한 곳에서 `기록 있음/없음` 또는 `실행 #` 형태로 낮춰 표시하게 했다.
- completed: EC2 `stockanalysis-web.service`에 배포했고 `/data-health`가 `200`으로 응답한다.

## Boundaries

- DB/API, scheduler, AI batch, alert destination, auth/RBAC, recommendation scoring, broker/order flow는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-operator-cockpit-ux-v3`
- passed: `git diff --check`
- passed: EC2 deploy and route/content smoke. Required terms `운영 판정판`, `수집/분석별 상태`, `품질 감사`, `가상 매매 검증`, `추천 산식 반영 비중`, `실거래 상태`, `벤치마크 괴리` present.
- passed: Playwright snapshot for `http://127.0.0.1:13000/data-health`; required terms present and visible forbidden terms `주문 경계`, `페이퍼 검증`, `추천 산식 가중치`, `벤치마크 drift`, `Active share`, `broker submit`, `threshold` absent.

## Exact Next Step

- exact next step: 다음 화면 `/trading-readiness`를 같은 방식으로 사용자용 문구와 판단 흐름 기준으로 정리한다.
