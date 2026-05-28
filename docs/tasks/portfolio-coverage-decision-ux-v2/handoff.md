# portfolio-coverage-decision-ux-v2 Handoff

## Status

- in progress: local implementation and verification passed; EC2 deploy and route smoke are next.

## Current Decision

- This is a frontend visibility slice only.
- The page already has detailed review, feedback, calibration, candidate, concentration, and position tables. The main gap is first-screen decision hierarchy.
- No scoring, broker, paper validation, portfolio, benchmark, or order state is mutated.

## Next Step

- exact next step: implement the `/portfolio/coverage` command panel and anchors, run local verification, deploy to EC2, smoke the tunnel route, then update this handoff with evidence.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-coverage-decision-ux-v2`
- passed: `git diff --check`

## Risks

- This task improves comprehension only. It does not create new portfolio decisions or outcome samples.
- Weight review remains blocked until mature outcome/feedback samples exist.
