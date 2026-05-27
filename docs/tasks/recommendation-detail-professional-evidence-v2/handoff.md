# recommendation-detail-professional-evidence-v2 Handoff

## Status

- in progress: local implementation and local verification passed. EC2 deploy and route smoke remain.

## Current Decision

- Build `professional_evidence_audit` from existing recommendation detail payloads rather than adding new schema or new write-side jobs.
- Keep this read-only. Recommendation weights, paper execution, and broker/order paths stay unchanged.

## Next Step

- exact next step: finish local verification, update review notes, then deploy to EC2 and smoke `/api/recommendations/{id}` plus `/recommendations/{id}`.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-detail-professional-evidence-v2`
- passed: `git diff --check`

## Risks

- This audit verifies whether professional evidence layers are present and visible; it does not prove valuation accuracy.
- Recommendation scoring weights, benchmark definitions, portfolio positions, broker submit, and live trading behavior were not changed.
