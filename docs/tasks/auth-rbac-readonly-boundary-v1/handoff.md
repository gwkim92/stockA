# auth-rbac-readonly-boundary-v1 Handoff

## Status

- status: implemented_and_ec2_smoked
- started_at: 2026-05-27
- current status: implemented, committed, pushed, deployed to EC2, and smoke verified.
- completed: local implementation, Python unit tests, compileall, Next typecheck/build, roadmap verify, AWH verify, GitHub push, EC2 fast-forward deploy, service restart, API smoke, and web route smoke.

## Current Decision

- 기존 `read-token`은 유지한다.
- 이 slice에서는 다중 사용자 계정/세션을 만들지 않는다.
- token은 `viewer` 기본 role을 가진 read-only principal로 해석한다.
- 모든 API write method와 broker/order flow는 계속 `read_only_no_order`로 차단한다.

## Next Step

- exact next step: continue with `alert-destination-free-channel-v1`; configure a free external alert destination and recent passed test artifact without exposing secrets.

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

## EC2 Verification

- deployed commit: `84e2cff`.
- `stockanalysis-frontend-api.service`: active.
- `stockanalysis-web.service`: active.
- `/__health`: `production live read-token read-only-token psycopg_pool`.
- `/api/data-health.auth_rbac`: `status=read_only_rbac_ready`, `attention_required=false`, `read_role=viewer`, `order_boundary=read_only_no_order`.
- `/api/data-health.open_gates`: `['alert_destination', 'portfolio_review_feedback_calibration_attention']`.
- `/data-health`: HTTP 200 and renders `읽기 전용 RBAC 확인` and `주문/쓰기 차단`.
