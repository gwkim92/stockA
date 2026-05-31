# performance-copy-polish-v3 handoff

## Status

- current status: in progress.
- completed: task contract created.

## Changes

- pending: polish `/performance` copy and labels so the page avoids raw internal terms and reads as a user-facing performance review.

## Verification

- pending: `cd apps/web && npm run typecheck`
- pending: `cd apps/web && npm run build`
- pending: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task performance-copy-polish-v3`
- pending: EC2 `/performance` route/content smoke.

## Exact Next Step

- exact next step: update `apps/web/src/app/performance/page.tsx` helper labels and visible copy.

## Notes

- frontend visibility only.
- recommendation weights, broker/order boundary, portfolio positions, benchmark, and outcome records are not changed.
