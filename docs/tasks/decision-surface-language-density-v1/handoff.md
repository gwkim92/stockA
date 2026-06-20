# decision-surface-language-density-v1 Handoff

## Current Status

- status: local implementation completed; Next typecheck, Next production build, and `git diff --check` passed; AWH re-check pending after this handoff update.
- in progress: local implementation and primary frontend verification are complete; final AWH verification, commit, push, EC2 deploy, and route smoke remain.
- branch: `develop`

## What Changed

- `/cycles` now leads with the cycle to inspect first and shorter risk-oriented copy.
- `/paper-trading` separates actual submitted orders, virtual validation, and blocked execution without explaining internal screen mechanics.
- `/portfolio/coverage` leads with portfolio risk gaps and outcome maturity boundary.
- `/performance` states that current outcome samples are not yet enough to change recommendation formulas.
- Recommendation detail copy now uses investor-facing evidence language instead of internal AI/process labels.

## Boundaries Preserved

- API contracts unchanged.
- Database schema unchanged.
- Scheduler cadence unchanged.
- Recommendation scoring weights unchanged.
- Benchmark definitions, portfolio positions, paper records, broker/order boundary, and live trading unchanged.
- Read-only/no-order boundary remains visible.

## Verification To Run

- exact next step: run `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-surface-language-density-v1`, then commit, push to `develop`, pull on EC2, restart `stockanalysis-web.service`, and route-smoke the touched pages.
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task decision-surface-language-density-v1`
- `git diff --check`

## EC2 Smoke Targets

- `/cycles`
- `/paper-trading`
- `/performance`
- `/portfolio/coverage`
- `/recommendations/<active recommendation id>`

## Remaining Risk

- This task improves copy density and decision hierarchy only. It does not redesign global navigation, chart composition, or information architecture beyond the touched pages.
