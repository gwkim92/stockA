# production-api-server-gate-evidence-v1 Handoff

## Status

- current status: implemented and EC2-smoked.
- completed: API payload, frontend visibility, gate policy, tests, Next typecheck/build, roadmap verify, AWH verify, EC2 deploy, and route smoke.

## Context

- EC2 FastAPI health evidence is already good:
  - `/__health` returned `runtime_profile=production`, `source_mode=live`, `auth_mode=read-token`, `connection_boundary=psycopg_pool`.
  - `/__ready` returned `database_pool.status=ok`.
- `/api/data-health` still listed `production_api_server` because the live adapter used a static open gate.

## Implemented Locally

- Added `production_api_server` payload to data-health.
- Added gate policy that closes the gate only when:
  - runtime profile is `production`.
  - source mode is `live`.
  - auth mode is `read-token`.
  - read token is configured.
  - allowed origin is explicit and not `*`.
  - DB config exists.
  - executor boundary is `psycopg_pool`.
- Added `/data-health` visibility for runtime, source, auth, CORS, DB boundary, and next action.

## Exact Next Step

- exact next step: continue with remaining open gates: `auth_rbac`, `alert_destination`, and `portfolio_review_feedback_calibration_attention`.

## Local Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter` -> `Ran 80 tests`, `OK`.
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests` -> passed.
- `cd apps/web && npm run typecheck` -> passed.
- `cd apps/web && npm run build` -> passed.
- `bash scripts/verify_project_execution_roadmap.sh` -> passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task production-api-server-gate-evidence-v1` -> passed.

## EC2 Verification

- deployed commit: `e238663`.
- services: `stockanalysis-frontend-api.service` active, `stockanalysis-web.service` active.
- `/__health`: `runtime_profile=production`, `source_mode=live`, `auth_mode=read-token`, `connection_boundary=psycopg_pool`.
- `/api/data-health`: `production_api_server.status=production_ready`, `attention_required=false`, `connection_boundary=psycopg_pool`.
- `/api/data-health.open_gates`: `['auth_rbac', 'alert_destination', 'portfolio_review_feedback_calibration_attention']`.
- `/data-health`: HTTP 200 and renders `운영 준비 확인`, `production · 실거래 · psycopg pool`, `read-token`, and the three remaining open gates.

## Guardrails

- This does not implement auth/RBAC.
- This does not configure TLS/reverse proxy/public domain.
- Recommendation weights, portfolio state, and order boundaries remain unchanged.
