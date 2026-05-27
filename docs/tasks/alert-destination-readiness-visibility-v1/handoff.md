# alert-destination-readiness-visibility-v1 Handoff

## Status

- current status: local implementation and verification passed; EC2 deploy/smoke remains.
- completed: local payload, frontend visibility, gate policy, tests, Next typecheck/build, roadmap verify.
- in progress: EC2 deploy and smoke.

## Context

- Remaining open gates after `production-api-server-gate-evidence-v1`: `auth_rbac`, `alert_destination`, `portfolio_review_feedback_calibration_attention`.
- `portfolio_review_feedback_calibration_attention` correctly waits for the 2026-06-24 outcome maturity window.
- `alert_destination` should not be closed until external notification delivery is configured and verified.

## Exact Next Step

- exact next step: deploy to EC2 and confirm `/api/data-health.alert_destination` explains missing external alert evidence while keeping `alert_destination` open.

## Implemented Locally

- Added `/api/data-health.alert_destination` payload.
- Added policy that closes `alert_destination` only when an external destination mode is configured, a destination target is configured, and a recent passed status artifact exists.
- Kept local-only modes such as `local_file`, `journal`, and `stdout` open because they cannot notify the operator when EC2 or schedulers fail.
- Added `/data-health` visibility for alert mode, target configured, test status, and next action.
- Added unit coverage for missing alert destination, local-only destination, external verified destination, and data-health gate removal.

## Local Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` -> `Ran 84 tests`, `OK`.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests` -> passed.
- `cd apps/web && npm run typecheck` -> passed.
- `cd apps/web && npm run build` -> passed.
- `bash scripts/verify_project_execution_roadmap.sh` -> passed.

## Guardrails

- Secrets stay outside the repo and are never rendered.
- Local-only alert sinks can be shown but cannot close the gate.
- Recommendation weights and broker/order flow remain unchanged.
