# auth-rbac-readonly-boundary-v1 Handoff

## Status

- status: implemented_pending_ec2_smoke
- started_at: 2026-05-27
- current status: implemented locally; Python unit tests, compileall, typecheck, Next build, roadmap verify, and AWH verify passed. EC2 deploy/smoke is still pending.
- in progress: EC2 deploy/smoke is still pending.

## Current Decision

- 기존 `read-token`은 유지한다.
- 이 slice에서는 다중 사용자 계정/세션을 만들지 않는다.
- token은 `viewer` 기본 role을 가진 read-only principal로 해석한다.
- 모든 API write method와 broker/order flow는 계속 `read_only_no_order`로 차단한다.

## Next Step

- exact next step: deploy to EC2 and confirm `/api/data-health` removes `auth_rbac` from `open_gates` when production read-token RBAC evidence is present.

## Implemented

- `FrontendRuntimePolicy` now exposes sanitized read-only RBAC metadata without leaking tokens.
- Protected FastAPI reads now authenticate into a read-only principal and unauthorized/write responses include stable read-only boundary details.
- `/api/data-health` now includes `auth_rbac` readiness and closes the gate only when production API evidence, bearer token, read-only role, write method block, and broker submit block are all true.
- `/data-health` now separates API runtime readiness from 권한 경계, 읽기 역할, and 주문/쓰기 차단.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_api_server tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `bash scripts/verify_project_execution_roadmap.sh`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task auth-rbac-readonly-boundary-v1`
