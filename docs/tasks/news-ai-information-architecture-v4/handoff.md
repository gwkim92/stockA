# news-ai-information-architecture-v4 Handoff

## Status

- in progress: local implementation and frontend verification are done; EC2 deployment and route smoke are next.

## Completed

- completed: created task contract.
- completed: reduced `/intelligence` fetch/default display sizes in local code.
- completed: added full-list CTAs for source news, AI candidates, structured results, and blocked candidates.
- completed: added AI evidence detail source preview fallback to prefer translated cluster events.

## Verification

- `cd apps/web && npm run typecheck`: passed locally.
- `cd apps/web && npm run build`: passed locally.
- `git diff --check`: passed locally.

## Next Step

- exact next step: rerun AWH verification, then deploy to EC2 and smoke `/intelligence` and `/ai-evidence/ai-evidence-251`.

## Notes

- This task is frontend information architecture only.
- Recommendation weights and order boundaries remain unchanged.
