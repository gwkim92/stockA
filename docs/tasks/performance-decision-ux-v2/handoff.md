# performance-decision-ux-v2 Handoff

## Status

- in progress: local implementation and verification passed; EC2 deploy and route smoke are next.

## Current Decision

- This is a frontend visibility slice only.
- The performance page should explain whether results are measurable and reliable before showing average alpha as a headline.
- No scoring, benchmark, portfolio, outcome, broker, paper validation, order, or weight-review state is mutated.

## Next Step

- exact next step: implement the `/performance` command panel and anchors, run local verification, deploy to EC2, smoke the tunnel route, then update this handoff with evidence.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task performance-decision-ux-v2`
- passed: `git diff --check`

## Risks

- This task improves comprehension only. It does not create new outcome samples or change calibration eligibility.
- Weight review remains governed by existing outcome maturity and feedback calibration gates.
