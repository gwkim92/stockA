# events-classification-decision-ux-v2 Handoff

## Status

- in progress: local implementation and verification passed; EC2 deploy and route smoke are next.

## Current Decision

- This is a frontend visibility slice only.
- The classification page should explain that rule-based first tags are preliminary and must be checked against AI evidence and validator output.
- No rule pack, AI extraction, validator, propagation, recommendation, broker, paper validation, order, or portfolio state is mutated.

## Next Step

- exact next step: implement the `/events/classification` command panel and anchors, run local verification, deploy to EC2, smoke the tunnel route, then update this handoff with evidence.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task events-classification-decision-ux-v2`
- passed: `git diff --check`

## Risks

- This task improves comprehension only. It does not improve classification accuracy.
- Richer per-event validator detail remains on AI evidence pages.
