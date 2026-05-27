# decision-cockpit-outcome-wait-visibility-v1 Handoff

## Status

- in progress: EC2 deploy and route smoke remain.
- local implementation complete; EC2 deploy and route smoke remain.

## Current Decision

- Use existing `/api/data-health.outcome_maturity_wait_monitor` on the home page.
- This is UX visibility only. It must not mutate recommendation weights, benchmark definitions, portfolio positions, paper execution, broker submit, or order flow.

## Next Step

- exact next step: commit and push the local UX change, pull it on EC2, rebuild/restart `stockanalysis-web.service`, and smoke `/` plus `http://127.0.0.1:13000/` for the outcome wait copy.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`

## Risks

- This does not create new outcome samples. It only makes the managed wait state visible earlier in the decision flow.
