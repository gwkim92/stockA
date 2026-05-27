# paper-trading-status-clarity-v2 Handoff

## Status

- in progress: local implementation and frontend verification are done; EC2 deployment and route smoke are next.

## Completed

- completed: created task contract.
- completed: added `/paper-trading` current-state summary for live order, simulation candidates, live conversion blocker, and next link.
- completed: clarified that paper actions are simulation candidates and not orders.
- completed: renamed candidate table language from virtual action to simulation action.

## Verification

- `cd apps/web && npm run typecheck`: passed locally.
- `cd apps/web && npm run build`: passed locally.
- `git diff --check`: passed locally.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task paper-trading-status-clarity-v2`: passed locally.

## Next Step

- exact next step: commit/push, deploy to EC2, then smoke `/paper-trading` on EC2 and local tunnel.

## Notes

- This task is frontend information architecture and copy only.
- Broker submit and live order flow must remain blocked.
