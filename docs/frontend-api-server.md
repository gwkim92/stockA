# Frontend API Server

이 문서는 production 후보 read-only frontend API server를 정의한다. 기존 stdlib fixture server는 local fixture/smoke 용도로 유지하고, 실제 API server 후보는 FastAPI + Uvicorn + psycopg pool을 사용한다.

## Current Status

- app factory: `src/stockanalysis/frontend/api_server.py`
- DB pool executor: `src/stockanalysis/frontend/db_pool.py`
- console script: `stockanalysis-frontend-api-server`
- verification: `scripts/verify_frontend_api_server.sh`
- deployment boundary: `docs/frontend-api-server-deployment-boundary.md`

## Runtime Environment

- `STOCKANALYSIS_DATABASE_URL`: psycopg pool connection string.
- `STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE`: `local` or `production`.
- `STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN`: CORS origin. Required and non-wildcard in production.
- `STOCKANALYSIS_FRONTEND_API_AUTH_MODE`: `disabled` or `read-token`.
- `STOCKANALYSIS_FRONTEND_API_READ_TOKEN`: bearer token for read API access.
- `STOCKANALYSIS_FRONTEND_API_REQUEST_TIMEOUT_SECONDS`: HTTP request timeout. Defaults to `30.0`.
- `STOCKANALYSIS_FRONTEND_API_OBSERVABILITY_MODE`: `disabled` or `otlp`. Defaults to `disabled`.
- `STOCKANALYSIS_FRONTEND_API_OTLP_ENDPOINT`: OTLP/HTTP Collector base endpoint. Required only when observability mode is `otlp`.

`STOCKANALYSIS_PSQL_COMMAND` remains supported for legacy CLI and stdlib runtime smoke paths. The FastAPI server uses `STOCKANALYSIS_DATABASE_URL` for pooled DB reads.

## Routes

- public: `/__live`
- public: `/__health`
- public: `/__ready`
- protected in `read-token` mode: `/__endpoints`
- protected in `read-token` mode: `/api/{path:path}`
- local profile only: `/openapi.json`, `/docs`

All write methods return stable `MethodNotAllowed` JSON. This server does not implement write APIs, thesis mutation, raw document download, or broker/order flow.

Collection endpoints support `limit` and opaque `cursor` parameters. Invalid pagination returns `FrontendPaginationInvalid` with HTTP 400.

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

## Observability And Probes

- Every response includes `X-Request-ID`.
- A safe inbound `X-Request-ID` is propagated; invalid or missing values are replaced with generated IDs.
- Access logs are one JSON object per request through `stockanalysis.frontend.api_server`.
- Timeout failures return `FrontendApiRequestTimeout` with the same stable error envelope and request id.
- `/__live` proves process liveness only.
- `/__ready` proves frontend contract readability and checks the psycopg pool when that boundary is active.
- Probe payloads expose public runtime metadata only; DB URL and read token are never included.
- External telemetry egress uses the OpenTelemetry Collector boundary defined in `docs/frontend-api-observability-sink-decision.md`.
- Optional OTLP exporter mode is documented in `docs/frontend-api-otel-exporter-pilot.md`.
- `/__health` exposes observability mode/runtime metadata but never exposes the OTLP endpoint.
- Access logs include bounded `route_template` and `status_class` fields. Raw query strings are not logged.

## Verification

```bash
bash scripts/verify_frontend_api_server.sh
bash scripts/verify_frontend_api_server_deployment_boundary.sh
bash scripts/verify_frontend_api_observability_sink_decision.sh
bash scripts/verify_frontend_api_otel_exporter_pilot.sh
```

The verification starts disposable Postgres, loads deterministic fixture state, starts Uvicorn/FastAPI in production profile, checks probes, request id propagation, unauthorized and authorized live DTO reads, then points Next.js at the FastAPI server for a production route smoke.

The deployment boundary verification checks repo-outside env template rendering, runtime env preflight, redaction, and `--preflight-only` wrapper behavior without connecting to production DB.

## Remaining Work

- SQL-level cursor seek optimization for large production lists.
- local Collector smoke and alert rules after deployment boundary accepts repo-owned sample config.
- full auth/RBAC and audited write boundary.
