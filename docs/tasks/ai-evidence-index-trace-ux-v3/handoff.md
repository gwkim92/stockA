# ai-evidence-index-trace-ux-v3 Handoff

## Status

- in progress: task contract created; implementation is next.

## Current Decision

- This is a frontend visibility slice only.
- `/ai-evidence` should read as the AI candidate workbench, not a final recommendation page.
- Candidate detail pages remain the place to inspect source news, Korean translation, AI fields, validator result, and recommendation linkage.
- No AI extraction, validator, scoring, recommendation, broker, paper validation, order, portfolio, or benchmark state is mutated.

## Next Step

- exact next step: add the `/ai-evidence` trace command panel and anchors, run local verification, deploy to EC2, smoke the tunnel route, then update this handoff with evidence.

## Verification So Far

- pending: local frontend verification.
- pending: AWH verification.
- pending: EC2/tunnel route smoke.

## Risks

- This task improves comprehension only. It does not improve AI extraction quality.
- Detailed validator and source evidence remain on individual AI evidence detail pages.
