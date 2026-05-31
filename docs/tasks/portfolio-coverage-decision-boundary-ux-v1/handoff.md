# portfolio-coverage-decision-boundary-ux-v1 handoff

## Status

- current status: completed.
- completed: local implementation, local verification, GitHub push, EC2 deploy, EC2 Next build, service restart, route content smoke, and Playwright DOM smoke.
- EC2 deploy/smoke: completed through commit `d865a261`.

## Changes

- `/portfolio/coverage` top decision panel now says `투자 논리 연결률`, `성과 측정`, and `추천 산식 변경 금지` instead of mixed internal terms.
- Replaced visible internal wording such as `thesis`, `outcome`, `weight`, `broker`, `feedback`, `calibration`, `cadence`, `action router`, `source 없음`, `paper validation`, and `active weight` in major user-facing areas.
- Order boundary labels now say `증권사 주문 금지/허용`.
- Review history, feedback, cadence, action router, rebalance, position sizing, and priority rationale now use Korean reason translation where available.
- Rebalance and position sizing sections now emphasize that rows are read-only review candidates, not order targets.

## Verification

- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-coverage-decision-boundary-ux-v1`
- Passed: `git diff --check`
- Passed on EC2: `npm run typecheck`
- Passed on EC2: `npm run build`
- Passed on EC2: `stockanalysis-web.service` active after restart.
- Passed route smoke: `/portfolio/coverage` returned `200`.
- Passed route content smoke: `투자 논리 연결률`, `성과 측정`, `추천 산식 변경 금지`, `증권사 주문·자동 리밸런싱·추천 산식 가중치 변경`, `사후평가와 누적평가`, `검토 실행 분기` rendered; `thesis 연결률`, `장기 outcome 기준`, `성과·weight 경계`, `weight 변경 금지`, `추천 weight`, `broker 주문`, `broker 전송`, `feedback과 calibration`, `cadence 없음`, `action router`, `source 없음`, `paper validation`, `active weight`, `결정 family` absent.
- Passed Playwright DOM smoke for `/portfolio/coverage` with the same positive and negative checks.

## Exact Next Step

- exact next step: continue the sequential UX pass on the next high-friction page group, likely `/data-health` or `/ai-evidence`, without changing recommendation weights or order boundaries.

## Notes

- 화면 가시성 개선만 수행한다.
- 추천 weight, broker/order boundary, portfolio state, benchmark는 변경하지 않는다.
