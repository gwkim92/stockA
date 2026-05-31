# events-copy-polish-v3 handoff

## Status

- current status: in progress.
- completed: task contract created.

## Changes

- pending: polish events copy and shared news event card labels.

## Verification

- pending: `cd apps/web && npm run typecheck`
- pending: `cd apps/web && npm run build`
- pending: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task events-copy-polish-v3`
- pending: EC2 `/events` and `/events/classification` route/content smoke.

## Exact Next Step

- exact next step: edit events pages and `NewsEventCard` visible labels.

## Notes

- frontend visibility only.
- AI extraction, validator, event classification, recommendation, and order logic are not changed.
