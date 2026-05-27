# portfolio-feedback-calibration-managed-wait-gate-v1 Handoff

## Status

- status: implemented_pending_ec2_smoke
- started_at: 2026-05-27
- current status: implemented locally and pending EC2 deploy/smoke.
- completed: managed wait policy for portfolio feedback calibration gate.
- completed: data-health wording now distinguishes managed wait from operational failure.

## Current Decision

- Treat immature outcome feedback as a managed wait when cadence/action-router explicitly say to wait and all order/weight guardrails are read-only.
- Do not treat this as approval to change recommendation scoring weights.

## Next Step

- exact next step: deploy to EC2, smoke `/api/data-health` and `/data-health`, then update this handoff with evidence.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task portfolio-feedback-calibration-managed-wait-gate-v1`
- passed: `git diff --check`
- pending: EC2 smoke.

## Risks

- If cadence/action-router evidence is missing or blocked, the gate must remain open.
- This task is visibility and gate classification only; it does not generate new outcome samples.
