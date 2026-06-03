# recommendation-decision-flow-clarity-v1 Handoff

## Current Status

- 진행 중: local verification passed; EC2 deploy and route smoke remain.
- 시작: 2026-06-03

## Scope

- `/recommendations`와 `/recommendations/[recommendationId]`의 사용자용 문구를 정리한다.
- 기능, API, 추천 산식, 포트폴리오, 주문 경계는 변경하지 않는다.

## Notes

- 직전 작업 `performance-portfolio-outcome-clarity-v1`은 성과/보유 리스크 화면의 혼선 문구를 정리하고 EC2 smoke까지 완료했다.
- 이번 작업은 추천 목록과 추천 상세의 남은 “후보/검토/판단/페이퍼” 혼선을 줄이는 후속 단계다.
- `/recommendations`와 `/recommendations/[recommendationId]`에서 사용자 화면에 직접 보일 수 있는 `판정`, `판단`, `검토`, `후보`, `페이퍼`, `AI 판단`, `AI 후보`, `보유 검토` 검색 결과는 0건이다.
- 변경은 Next.js page copy와 metadata에 한정했다. API contract, 추천 weight, benchmark, portfolio position, performance outcome, 가상 매매 기록, broker/order boundary는 변경하지 않았다.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`

## Next Step

- exact next step: commit and push the local UX copy changes, deploy the branch on EC2, restart `stockanalysis-web.service`, then smoke `/recommendations` and one live `/recommendations/[id]` route through `http://127.0.0.1:13000`.
