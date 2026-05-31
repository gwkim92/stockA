# ai-evidence-blocked-ux-v3 Handoff

## Status

- in progress: task contract created; implementation is next.

## Current Decision

- This is a frontend visibility slice only.
- `/ai-evidence/blocked` should explain why candidates are excluded and where to inspect them, not provide approval controls.
- No AI extraction, validator, propagation, scoring, recommendation, broker, paper validation, order, portfolio, or benchmark state is mutated.

## Next Step

- exact next step: add the blocked-candidate command panel, run local verification, deploy to EC2, smoke the tunnel route, then update this handoff with evidence.

## Verification So Far

- pending: local frontend verification.
- pending: AWH verification.
- pending: EC2/tunnel route smoke.

## Risks

- This task improves comprehension only. It does not change which AI candidates are blocked or suppressed.
- Remediation still requires backend rule/alias/classification work in separate tasks.
