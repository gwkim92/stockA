# professional-recommendation-coverage-audit-v1 Handoff

## Status

- in progress: local implementation and verification complete. EC2 deploy and route smoke pending.

## Current Decision

- Implement as data-health visibility over existing canonical recommendation/professional coverage tables.
- Keep this read-only. Recommendation weights, paper execution, and broker/order paths stay unchanged.

## Next Step

- exact next step: deploy to EC2, restart services, smoke `/api/data-health` and `/data-health`.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task professional-recommendation-coverage-audit-v1`
- passed: `git diff --check`
- pending: EC2 route smoke.

## Risks

- This audit does not prove the valuation model is correct; it proves whether required evidence layers are attached and whether blockers are visible.
