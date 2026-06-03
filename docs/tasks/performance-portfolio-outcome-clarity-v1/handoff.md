# performance-portfolio-outcome-clarity-v1 Handoff

## Current Status

- 완료: local verification, GitHub push, EC2 deploy, EC2 route smoke, tunnel route smoke, and Playwright DOM smoke passed.
- 시작: 2026-06-03

## Scope

- `/performance`와 `/portfolio/coverage`의 사용자용 문구를 정리한다.
- 기능, API, 추천 산식, 포트폴리오, 주문 경계는 변경하지 않는다.

## Notes

- 이전 UX 정리 작업은 `/events`, `/source-documents`, `/ai-evidence`, `/intelligence`, `/data-health`까지 완료됐다.
- 이번 작업은 성과 측정과 보유 리스크 화면의 남은 “검토/페이퍼/후보/판단” 혼선을 줄이는 후속 단계다.
- `/performance`와 `/portfolio/coverage`에서 사용자 화면에 직접 보일 수 있는 `검토`, `후보`, `페이퍼`, `AI 판단`, `AI 후보`, `보유 검토`, `판단` 검색 결과는 0건이다.
- 변경은 Next.js page copy와 metadata에 한정했다. API contract, 추천 weight, benchmark, portfolio position, performance outcome, 가상 매매 기록, broker/order boundary는 변경하지 않았다.
- EC2는 commit `69a27c5`로 fast-forward 됐고 `stockanalysis-web.service`를 재시작했다.
- `/performance`는 `보유·리스크 상태 열기`, `성과 해석 기준`, `보유 상태-성과 충돌`을 렌더링한다.
- `/portfolio/coverage`는 `보유·리스크 상태`, `리밸런싱 확인 대상`, `포트폴리오 결정 신뢰도`, `보유 종목 상태 지도`를 렌더링한다.

## Verification

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task performance-portfolio-outcome-clarity-v1`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-web.service stockanalysis-frontend-api.service` returned `active active`.
- passed on EC2: `http://127.0.0.1:3000/performance` and `/portfolio/coverage` route smoke found the updated Korean copy.
- passed through local tunnel: `http://127.0.0.1:13000/performance` and `/portfolio/coverage` route smoke found the updated Korean copy.
- passed via Playwright DOM smoke: `http://127.0.0.1:13000/performance` and `/portfolio/coverage` exposed the updated Korean text.

## Next Step

- exact next step: continue the UX/UI refactor with `/recommendations` list and `/recommendations/[id]`, because those pages still need the same user-facing decision hierarchy and wording pass.
