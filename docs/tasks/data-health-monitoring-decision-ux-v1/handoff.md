# data-health-monitoring-decision-ux-v1 handoff

## Status

- current status: in progress.
- completed: task contract created.

## Changes

- pending: update `/data-health` first-screen monitoring copy and major decision-boundary sections.

## Verification

- pending: `cd apps/web && npm run typecheck`
- pending: `cd apps/web && npm run build`
- pending: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-health-monitoring-decision-ux-v1`
- pending: EC2 `/data-health` route/content smoke.

## Exact Next Step

- exact next step: edit data health page copy so collection status, AI quality, outcome wait, recommendation weight, and broker order boundaries are shown in Korean user terms.

## Notes

- 화면 가시성 개선만 수행한다.
- 추천 weight, broker/order boundary, scheduler cadence, pipeline runners는 변경하지 않는다.
