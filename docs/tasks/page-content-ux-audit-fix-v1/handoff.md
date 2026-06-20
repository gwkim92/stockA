# page-content-ux-audit-fix-v1 Handoff

## Status

- in progress: route inventory completed, first UI audit completed, home duplicate remediation CTAs reduced, Korean labels for English AI eval cases and runner names patched, and local frontend verification passed. EC2 deploy and live route smoke are next.

## Findings

- `/` renders too many repeated remediation group cards and the same `보완 큐에서 처리` CTA appears dozens of times.
- `/data-health` still exposes some fixture case IDs and backend runner names in English, for example `direct nvda ai chip news`, `energy shock exxon direct`, and `low signal should block`.
- Current data analysis state is not treated as perfect: source limits and outcome maturity waits remain visible and should not be hidden.

## Current Scope

- Keep this as display/wording/visibility work only.
- Do not modify recommendation scoring, benchmark definitions, portfolio positions, schema, or broker/order boundaries.

## Next Step

- exact next step: commit and push to `develop`, deploy the same commit to EC2, restart the web service, and run live route smoke for `/`, `/data-health`, `/intelligence`, `/ai-evidence`, `/cycle-map`, `/recommendations`, `/stocks`, and `/paper-trading`.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task page-content-ux-audit-fix-v1`

## Remaining Risks

- This pass improves page wording and density only. It does not redesign every page from scratch.
- EC2 live data may still show legitimate source limits, managed waits, or blocked recommendations; those should remain visible rather than hidden.
