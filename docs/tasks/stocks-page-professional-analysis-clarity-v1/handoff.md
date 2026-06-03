# stocks-page-professional-analysis-clarity-v1 Handoff

## Status

- in progress: local implementation and local verification completed; EC2 route/browser smoke pending.

## Scope

- Frontend stock detail clarity only.
- No backend API, DB schema, scoring, benchmark, portfolio, scheduler, AI batch, broker, or live order changes.

## Current Decision

- Derive a compact stock-level professional evidence audit from existing page data instead of adding new API fields.
- Show the audit near the top of `/stocks/{symbol}` so the user can see complete, partial, pending, blocked, missing, and not-applicable evidence layers before scrolling through detailed panels.
- Keep ETF/fund instruments separate from operating-company financial statement requirements.

## Verification So Far

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task stocks-page-professional-analysis-clarity-v1`
- passed: `git diff --check`
- pending: EC2 route smoke.

## Next Step

- exact next step: commit, push, deploy to EC2, restart the web service, and verify `/stocks/ARM`, `/stocks/SPY`, `/stocks/EROK`, plus the tunnel route.
