# stocks-page-professional-analysis-clarity-v1 Handoff

## Status

- completed: stock detail professional evidence audit is implemented, committed, pushed, deployed to EC2, and route/browser smoke passed.

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
- passed on EC2: `npm run typecheck`
- passed on EC2: `npm run build`
- passed on EC2: `systemctl is-active stockanalysis-web.service`
- passed on EC2: route smoke for `/stocks/ARM`, `/stocks/SPY`, and `/stocks/EROK`.
- passed through user tunnel: `http://127.0.0.1:13000/stocks/ARM`, `/stocks/SPY`, and `/stocks/EROK` render the stock professional evidence audit, ETF/fund boundary, source-blocked boundary, and read-only order status copy.

## Next Step

- exact next step: continue page-by-page UX refactor with `ai-evidence-visibility-v3` so source news, Korean translation, AI structure, validator result, propagation path, and recommendation connection are visible in one trace.
