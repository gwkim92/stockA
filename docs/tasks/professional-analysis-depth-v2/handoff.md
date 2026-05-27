# professional-analysis-depth-v2 Handoff

## Status

- status: local_verified
- started_at: 2026-05-27
- current status: local implementation and verification complete.
- in progress: EC2 deploy and live smoke pending.

## Current Decision

- Use the existing data-health live SQL and professional source gap CTEs.
- Add read-only depth visibility only. Do not mutate scoring, benchmark, portfolio, broker, or order state.

## Next Step

- exact next step: deploy to EC2, restart FastAPI/Next services, and smoke `/api/data-health` plus `/data-health`.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task professional-analysis-depth-v2`
- passed: `git diff --check`
- pending: EC2 smoke.

## Risks

- Depth is only as accurate as the existing active recommendation and source coverage tables.
- Source-blocked symbols must stay blocked rather than being filled with synthetic data.
- This task is visibility-only. Recommendation scoring weights, benchmark definitions, portfolio positions, and broker/order flow are unchanged.
