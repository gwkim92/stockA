# Frontend API Runtime Boundary

이 문서는 frontend read-only HTTP runtime의 production-facing boundary를 정의한다. 현재 runtime은 Python stdlib 기반 local server지만, non-local/prod 실행이 실수로 열리지 않도록 startup policy를 적용한다.

## Current Status

- runtime policy module: `src/stockanalysis/frontend/runtime_policy.py`
- HTTP runtime module: `src/stockanalysis/frontend/fixture_server.py`
- default profile: `local`
- default source: `fixture`
- default auth: disabled, loopback host only
- production profile: guarded startup only

## Runtime Profiles

`local` profile:

- default profile.
- unauthenticated startup is allowed only on loopback hosts: `127.0.0.1`, `localhost`, `::1`.
- `fixture`, `auto`, `live` source modes are allowed.
- detailed adapter error messages are allowed for local debugging.

`production` profile:

- `fixture` source is rejected.
- `auth_mode=read-token` is required.
- explicit CORS allowed origin is required.
- `STOCKANALYSIS_PSQL_COMMAND` is required for `live` or `auto` source.
- detailed adapter error messages are suppressed.

## Environment Variables

- `STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE`: `local` or `production`.
- `STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN`: CORS origin. Required and non-wildcard in production profile.
- `STOCKANALYSIS_FRONTEND_API_AUTH_MODE`: `disabled` or `read-token`.
- `STOCKANALYSIS_FRONTEND_API_READ_TOKEN`: bearer token for `read-token` mode.
- `STOCKANALYSIS_PSQL_COMMAND`: live read DB command. Required for production `live`/`auto` source.

## CLI

Local fixture runtime:

```bash
PYTHONPATH=src python3 -m stockanalysis.frontend.fixture_server \
  --host 127.0.0.1 \
  --port 8765
```

Local read-token protected runtime:

```bash
STOCKANALYSIS_FRONTEND_API_READ_TOKEN='replace-me' \
PYTHONPATH=src python3 -m stockanalysis.frontend.fixture_server \
  --host 127.0.0.1 \
  --port 8765 \
  --auth-mode read-token
```

Production-profile guarded runtime:

```bash
STOCKANALYSIS_FRONTEND_API_READ_TOKEN='replace-me' \
STOCKANALYSIS_PSQL_COMMAND='psql postgresql://...' \
PYTHONPATH=src python3 -m stockanalysis.frontend.fixture_server \
  --host 127.0.0.1 \
  --port 8765 \
  --source auto \
  --runtime-profile production \
  --allowed-origin https://cockpit.example \
  --auth-mode read-token
```

Console script aliases:

- `stockanalysis-frontend-fixture-server`
- `stockanalysis-frontend-runtime-server`

Both point to the same runtime. The alias exists so future deployment docs can stop referring to the runtime as fixture-only.

## Auth Boundary

`read-token` mode requires:

```http
Authorization: Bearer <token>
```

Protected:

- `/__endpoints`
- `/api/...`

Public:

- `/__health`
- `OPTIONS` preflight

This is not full RBAC. It is a deployment safety seam until real identity, role mapping, sessions, and audit trail are implemented.

## Security Decisions

- no database credentials in browser.
- no API keys in frontend bundle.
- no write endpoints.
- no raw source document download enablement.
- no broker/order flow.
- no hidden thesis mutation.
- production profile refuses wildcard CORS.
- production profile refuses fixture source.

## Verification

```bash
bash scripts/verify_frontend_api_runtime_boundary.sh
bash scripts/verify_frontend_runtime_db_smoke.sh
bash scripts/verify_frontend_api_server.sh
```

검증은 아래를 확인한다.

- default fixture server behavior remains intact.
- local non-loopback unauthenticated startup is rejected.
- read-token auth protects `/api/...`.
- health remains public and exposes safe runtime metadata.
- production profile rejects unguarded startup.
- production profile accepts guarded `auto` runtime metadata when DB command and token are configured.
- disposable Postgres-backed `source=live` HTTP runtime returns representative frontend DTOs with bearer-token auth.
- FastAPI server uses psycopg pool and preserves the same read-token/API boundary.

## Remaining Work

- request id, timeout, structured logs, readiness probes, and deployment hardening.
- real auth/RBAC with viewer, analyst, operator, admin roles.
- audited write command boundary after auth/RBAC.
