# stocks-list-decision-ux-v2 Handoff

## Status

- in progress: local implementation and verification passed; EC2 deploy and route smoke are next.

## Current Decision

- This is a frontend visibility slice only.
- The stock list API does not expose professional source blocker counts. The list should not invent those counts; it should route users to stock detail for professional/source evidence.
- No scoring, broker, paper validation, portfolio, benchmark, or order state is mutated.

## Next Step

- exact next step: implement the `/stocks` command panel, run local verification, deploy to EC2, smoke the tunnel route, then update this handoff with evidence.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stocks-list-decision-ux-v2`
- passed: `git diff --check`

## Risks

- This task improves comprehension only. It does not add professional source blocker data to the stock list API.
- If users need source-blocked counts directly on `/stocks`, that should be a separate backend/API visibility task.
