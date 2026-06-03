# recommendation-evidence-quality-audit-v1 Handoff

## Status

- in progress: local implementation and verification are partially complete; EC2 deploy and smoke are still pending.

## Scope

- Read-only recommendation evidence quality visibility.
- No scoring, benchmark, portfolio, broker, or live order changes.

## Current Decision

- Reuse the existing recommendation list read adapter instead of adding schema or write jobs.
- Keep detail-level `professional_evidence_audit` as the deep drilldown and add only a compact list-level `evidence_quality` summary.

## Verification So Far

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- pending: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-evidence-quality-audit-v1`
- pending: EC2 deploy and route smoke.

## Next Step

- exact next step: run AWH verification, deploy to EC2, and confirm `/api/recommendations` plus `/recommendations` render the evidence quality summary.
