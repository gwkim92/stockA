# professional-analysis-next-action-cockpit-v1 Handoff

## Status

- status: implemented_pending_ec2_smoke
- started_at: 2026-05-27
- current status: implemented locally and pending EC2 deploy/smoke.
- completed: API payload `professional_analysis_next_action`.
- completed: `/data-health` professional next-action section.

## Current Decision

- Build the summary from existing canonical data-health payloads instead of adding new database tables.
- Keep EROK-like source blockers visible but already excluded from professional decision and paper validation inputs.

## Next Step

- exact next step: deploy to EC2, confirm API payload and route rendering, then update this handoff with smoke evidence.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task professional-analysis-next-action-cockpit-v1`
- passed: `git diff --check`
- pending: EC2 smoke.

## Risks

- This cockpit summarizes existing evidence only. It does not fix source-blocked symbols or create new valuation artifacts.
