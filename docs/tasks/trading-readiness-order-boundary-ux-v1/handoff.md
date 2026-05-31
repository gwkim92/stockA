# trading-readiness-order-boundary-ux-v1 handoff

## Status

- current status: in progress.
- completed: task contract created.

## Changes

- pending: update `/trading-readiness` Korean decision copy and order boundary visibility.

## Verification

- pending: `cd apps/web && npm run typecheck`
- pending: `cd apps/web && npm run build`
- pending: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task trading-readiness-order-boundary-ux-v1`
- pending: EC2 `/trading-readiness` route/content smoke.

## Exact Next Step

- exact next step: edit trading readiness page copy so broker submit, kill switch, audit, and paper validation states are shown as Korean safety boundaries.

## Notes

- 화면 가시성 개선만 수행한다.
- 추천 weight, broker/order boundary, portfolio state, benchmark는 변경하지 않는다.
