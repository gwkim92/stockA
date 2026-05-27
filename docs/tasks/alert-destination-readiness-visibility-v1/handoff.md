# alert-destination-readiness-visibility-v1 Handoff

## Status

- current status: implemented and EC2-smoked.
- completed: payload, frontend visibility, gate policy, tests, local verification, AWH verify, GitHub push, EC2 deploy, service restart, API smoke, and route smoke.

## Context

- Remaining open gates after `production-api-server-gate-evidence-v1`: `auth_rbac`, `alert_destination`, `portfolio_review_feedback_calibration_attention`.
- `portfolio_review_feedback_calibration_attention` correctly waits for the 2026-06-24 outcome maturity window.
- `alert_destination` should not be closed until external notification delivery is configured and verified.

## Exact Next Step

- exact next step: continue with `auth_rbac` or configure a free external alert destination and write a passed status artifact outside the repo.

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
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task alert-destination-readiness-visibility-v1` -> passed.

## EC2 Verification

- deployed commit: `dad38e4`.
- services: `stockanalysis-frontend-api.service` active, `stockanalysis-web.service` active.
- `/api/data-health.alert_destination`: `status=missing_destination`, `attention_required=true`, `mode=missing`, `target_configured=false`, `last_test_status=missing`.
- `/api/data-health.open_gates`: `['auth_rbac', 'alert_destination', 'portfolio_review_feedback_calibration_attention']`.
- `/data-health`: HTTP 200 and renders `운영 알림 확인 필요`, `알림 목적지`, `외부 알림 목적지가 설정되지 않았다`, `알림 설정 보기`.

## Guardrails

- Secrets stay outside the repo and are never rendered.
- Local-only alert sinks can be shown but cannot close the gate.
- Recommendation weights and broker/order flow remain unchanged.
