# events-ledger-decision-ux-v2 Handoff

## Status

- in progress: local implementation and verification passed; EC2 deploy and route smoke are next.

## Current Decision

- This is a frontend visibility slice only.
- The raw event ledger should explain the processing path before showing the long list.
- No AI extraction, validator, propagation, recommendation, broker, paper validation, order, or portfolio state is mutated.

## Next Step

- exact next step: implement the `/events` command panel and anchors, run local verification, deploy to EC2, smoke the tunnel route, then update this handoff with evidence.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task events-ledger-decision-ux-v2`
- passed: `git diff --check`

## Risks

- This task improves comprehension only. It does not improve event classification or AI extraction quality.
- The event list shows current API fields only; richer per-event validator detail remains on AI evidence pages.
