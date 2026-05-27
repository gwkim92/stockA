# auth-rbac-readonly-boundary-v1 Contract

## Task Request

- request: EC2 운영 후보 상태에서 `auth_rbac` gate를 정적 open gate가 아니라 검증 가능한 read-only 권한 경계로 전환한다.
- context: FastAPI production/live/read-token/psycopg_pool gate는 닫혔지만, `/api/data-health`는 아직 `auth_rbac`를 generic open gate로 남긴다. 지금 단계에서 쓰기 API, 주문 API, broker submit은 열면 안 된다.

## Goal

- goal: `/__endpoints`와 `/api/...`는 bearer token이 있어야 읽히고, token은 read-only role boundary를 가진다. `/api/data-health`는 `auth_rbac` evidence를 보여주고, production read-only role boundary가 확인될 때만 `auth_rbac` gate를 닫는다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/runtime_policy.py`
  - `src/stockanalysis/frontend/api_server.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/data-health/page.tsx`
  - `tests/test_frontend_api_server.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/auth-rbac-readonly-boundary-v1/*`

## Invariants

- Do not add write endpoints.
- Do not enable broker submit, automatic order, automatic rebalance, or portfolio mutation.
- Do not expose bearer tokens, webhook URLs, DB URLs, or secret env values in API responses or logs.
- Do not change recommendation scoring weights, benchmark composition, portfolio positions, thesis state, or outcome calibration policy.
- Local fixture/smoke runtime must continue to work.

## Scope

- Add a read-only role boundary around the existing read-token authentication.
- Expose sanitized auth/RBAC readiness in `public_metadata`, `/__health`, `/__ready`, and `/api/data-health`.
- Close `auth_rbac` only when production API evidence and read-only role boundary are both present.
- Show the boundary on `/data-health` in Korean user-facing wording.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_api_server tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task auth-rbac-readonly-boundary-v1`
