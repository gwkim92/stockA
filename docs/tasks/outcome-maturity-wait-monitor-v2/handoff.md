# outcome-maturity-wait-monitor-v2 Handoff

## Status

- in progress: local implementation and local verification passed. EC2 deploy and route smoke remain.

## Current Decision

- Add a derived data-health DTO rather than a new backend runner. Existing outcome maturity and feedback calibration artifacts already hold the source of truth.
- Keep the monitor read-only. It can explain when to wait or when to run calibration, but it must not mutate scoring weights or execute broker/order flows.

## Next Step

- exact next step: deploy to EC2 and smoke `/api/data-health` plus `/data-health`.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task outcome-maturity-wait-monitor-v2`
- passed: `git diff --check`

## Risks

- This monitor improves visibility only. It does not create new outcome samples.
- Weight review remains blocked until due outcome windows and mature feedback samples exist.
