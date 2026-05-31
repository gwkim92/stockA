# portfolio-coverage-decision-boundary-ux-v1 handoff

## Status

- current status: in progress.
- completed: task contract created.

## Changes

- pending: update `/portfolio/coverage` Korean decision copy and read-only boundary visibility.

## Verification

- pending: `cd apps/web && npm run typecheck`
- pending: `cd apps/web && npm run build`
- pending: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-coverage-decision-boundary-ux-v1`
- pending: EC2 `/portfolio/coverage` route/content smoke.

## Exact Next Step

- exact next step: edit portfolio coverage page copy so portfolio review, risk budget, rebalance candidates, outcome maturity, recommendation weight, and broker order boundaries are shown in Korean user terms.

## Notes

- 화면 가시성 개선만 수행한다.
- 추천 weight, broker/order boundary, portfolio state, benchmark는 변경하지 않는다.
