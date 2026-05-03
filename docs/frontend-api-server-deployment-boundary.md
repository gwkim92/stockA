# Frontend API Server Deployment Boundary

이 문서는 FastAPI read-only frontend API server의 production 후보 배포 경계를 정의한다. 실제 secret, host service manager config, reverse proxy config, TLS material은 repo에 저장하지 않는다.

## Current Status

- env template renderer: `scripts/render_frontend_api_server_env_template.sh`
- runtime env checker: `scripts/check_frontend_api_server_runtime_env.sh`
- env-based run wrapper: `scripts/run_frontend_api_server.sh`
- verification: `scripts/verify_frontend_api_server_deployment_boundary.sh`

## Topology

Production 후보 topology는 아래를 기본으로 한다.

```text
browser
  -> HTTPS reverse proxy / managed edge
  -> loopback FastAPI frontend API server
  -> psycopg pool
  -> Postgres
```

Boundary rules:

- FastAPI server binds loopback only: `127.0.0.1`, `localhost`, or `::1`.
- Public TLS termination belongs to reverse proxy or managed edge, not the Python process.
- Reverse proxy must forward `Authorization` and `X-Request-ID`.
- Reverse proxy must not cache `/api/...`, `/__health`, `/__ready`, or `/__live`.
- `/__live`, `/__health`, and `/__ready` can be used by process managers and load balancers.
- `/api/...` and `/__endpoints` still require bearer token in `read-token` mode.

## Runtime Env Template

Render a template outside the repository:

```bash
bash scripts/render_frontend_api_server_env_template.sh \
  --output /absolute/outside/repo/frontend-api-server.env
```

The renderer refuses repo-internal output and writes the file with mode `600`.

Edit the rendered file outside the repo and replace placeholders. Required values include:

- `STOCKANALYSIS_DATABASE_URL`
- `STOCKANALYSIS_FRONTEND_RUNTIME_PROFILE=production`
- `STOCKANALYSIS_FRONTEND_API_ALLOWED_ORIGIN=https://...`
- `STOCKANALYSIS_FRONTEND_API_AUTH_MODE=read-token`
- `STOCKANALYSIS_FRONTEND_API_READ_TOKEN`
- `STOCKANALYSIS_FRONTEND_API_HOST=127.0.0.1`
- `STOCKANALYSIS_FRONTEND_API_PORT=8787`

## Readiness Check

Run the preflight without connecting to the DB:

```bash
bash scripts/check_frontend_api_server_runtime_env.sh \
  --env-file /absolute/outside/repo/frontend-api-server.env
```

It checks:

- env file is outside the repo
- required variables exist
- placeholder values were replaced
- runtime profile is `production`
- auth mode is `read-token`
- allowed origin is explicit HTTPS
- API bind host is loopback
- DB URL has postgres/postgresql shape, host, database, and user
- read token is configured and at least 32 characters
- port, pool sizes, and timeout values are valid
- optional repo root contains `docs/api/frontend/contract-index.json`

The JSON output redacts DB URL and read token.

## Run Wrapper

Preflight only:

```bash
bash scripts/run_frontend_api_server.sh \
  --env-file /absolute/outside/repo/frontend-api-server.env \
  --preflight-only
```

Run server:

```bash
bash scripts/run_frontend_api_server.sh \
  --env-file /absolute/outside/repo/frontend-api-server.env
```

The wrapper runs the env checker first, then executes:

```bash
python -m stockanalysis.frontend.api_server ...
```

## Boundaries

- Does not install launchd/systemd units.
- Does not write Docker/Kubernetes manifests.
- Does not write reverse proxy config.
- Does not generate or store TLS certificates.
- Does not commit env files or credentials.
- Does not add write APIs, full auth/RBAC, or broker/order flow.

## Verification

```bash
bash scripts/verify_frontend_api_server_deployment_boundary.sh
```

This verifies script syntax, repo-internal output rejection, unedited template failure, valid temp env success, run-wrapper preflight, and redaction of DB URL/read token.
