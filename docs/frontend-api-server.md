# Frontend API Server

이 문서는 production 후보 read-only frontend API server를 정의한다. 기존 stdlib fixture server는 local fixture/smoke 용도로 유지하고, 실제 API server 후보는 FastAPI + Uvicorn + psycopg pool을 사용한다.

## Current Status

- app factory: `src/stockanalysis/frontend/api_server.py`
- DB pool executor: `src/stockanalysis/frontend/db_pool.py`
- console script: `stockanalysis-frontend-api-server`
- verification: `scripts/verify_frontend_api_server.sh`

## Runtime Environment

- `STOCKANALYSIS_DATABASE_URL`: psycopg pool connection string.
- `STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE`: `local` or `production`.
- `STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN`: CORS origin. Required and non-wildcard in production.
- `STOCKANALYSIS_FRONTEND_API_AUTH_MODE`: `disabled` or `read-token`.
- `STOCKANALYSIS_FRONTEND_API_READ_TOKEN`: bearer token for read API access.

`STOCKANALYSIS_PSQL_COMMAND` remains supported for legacy CLI and stdlib runtime smoke paths. The FastAPI server uses `STOCKANALYSIS_DATABASE_URL` for pooled DB reads.

## Routes

- public: `/__health`
- protected in `read-token` mode: `/__endpoints`
- protected in `read-token` mode: `/api/{path:path}`
- local profile only: `/openapi.json`, `/docs`

All write methods return stable `MethodNotAllowed` JSON. This server does not implement write APIs, thesis mutation, raw document download, or broker/order flow.

## Command

```bash
STOCKANALYSIS_DATABASE_URL='postgresql://...' \
STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE=production \
STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN='https://cockpit.example' \
STOCKANALYSIS_FRONTEND_API_AUTH_MODE=read-token \
STOCKANALYSIS_FRONTEND_API_READ_TOKEN='replace-me' \
stockanalysis-frontend-api-server \
  --host 127.0.0.1 \
  --port 8787
```

## Next.js Integration

`apps/web` reads `STOCKANALYSIS_FRONTEND_API_BASE_URL` server-side. If `STOCKANALYSIS_FRONTEND_API_READ_TOKEN` is present, the server component fetch adapter sends `Authorization: Bearer <token>`.

Do not expose this token through `NEXT_PUBLIC_*`.

## Verification

```bash
bash scripts/verify_frontend_api_server.sh
```

The verification starts disposable Postgres, loads deterministic fixture state, starts Uvicorn/FastAPI in production profile, checks unauthorized and authorized live DTO reads, then points Next.js at the FastAPI server for a production route smoke.

## Remaining Work

- request id and structured logs.
- timeout and cancellation policy.
- readiness and liveness probes.
- deployment manifests.
- full auth/RBAC and audited write boundary.
