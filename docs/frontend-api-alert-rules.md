# Frontend API Alert Rules

## Decision

`frontend-api-alert-rules` adds a secret-free Prometheus-compatible alert rule reference for the read-only FastAPI frontend API server.

The rule file is `ops/observability/frontend-api-alert-rules.yml`. It is a repository reference, not a deployment manifest. Alertmanager receiver destinations, credentials, contact channels, silence policy, and environment-specific routing stay outside this public repository.

## Runtime Assumptions

- The application exports OTLP telemetry only when `STOCKANALYSIS_FRONTEND_API_OBSERVABILITY_MODE=otlp` is enabled.
- An OpenTelemetry Collector or equivalent pipeline converts the bounded frontend API metrics into Prometheus-compatible series.
- The scrape job label is `job="stockanalysis-frontend-api"`.
- Public probes remain `/__live`, `/__health`, and `/__ready`; no public `/metrics` endpoint is introduced by this task.
- Current app code has the OTLP/export boundary and local receiver smoke. Production Collector installation and managed alert routing are separate tasks.

## Metrics

The alert rules use only bounded frontend API runtime metrics:

- `frontend_api_requests_total`
- `frontend_api_request_duration_seconds_bucket`
- `frontend_api_request_timeouts_total`
- `frontend_api_adapter_errors_total`
- `frontend_api_ready`
- `frontend_api_db_pool_ready`

Allowed selector labels remain bounded: `job`, `route_template`, `method`, `status_class`, `profile`, `source_mode`, `error_code`, and histogram `le`.

Forbidden labels and rule content:

- request id
- raw query string
- raw SQL text
- DB URL
- bearer token or auth secret
- ticker/symbol
- portfolio name
- document id
- thesis id
- recommendation id
- arbitrary request path segment
- Slack, email, PagerDuty, OpsGenie, webhook, or other receiver config

## Alerts

### FrontendApiDown

Condition: scrape target is down or absent for 5 minutes.

Operator action: check process supervisor, Uvicorn startup logs, loopback binding, reverse proxy health target, and runtime env preflight output.

### FrontendApiNotReady

Condition: `frontend_api_ready` or `frontend_api_db_pool_ready` is 0 for 5 minutes.

Operator action: check database reachability, `STOCKANALYSIS_DATABASE_URL`, pool startup `wait()`, migration status, and `/__ready` response.

### FrontendApiHigh5xxRate

Condition: 5xx requests exceed 5 percent of read-only frontend API traffic for 10 minutes.

Operator action: inspect structured logs by `route_template`, `status_class`, and `error_code`. Do not add raw paths or request ids as metric labels.

### FrontendApiTimeoutSpike

Condition: timeout count exceeds 3 events over 10 minutes.

Operator action: inspect DB latency, pool saturation, upstream runtime resource pressure, and endpoint-specific structured logs.

### FrontendApiHighLatency

Condition: p95 request latency remains above 2 seconds for 10 minutes.

Operator action: compare dashboard/list/detail endpoints separately, then check query plans only in an operator-owned environment. Do not expose SQL text in alert labels.

### FrontendApiAdapterErrorSpike

Condition: adapter error count exceeds 5 events over 10 minutes.

Operator action: inspect stable error code distribution, recent deployment changes, and database read shape compatibility.

## Verification

Run:

```bash
bash scripts/verify_frontend_api_alert_rules.sh
```

This validates the rule file with `scripts/validate_frontend_api_alert_rules.py`, checks the expected six alert rules, blocks receiver/secret strings, and enforces bounded PromQL selector labels.

## Not Implemented

- Alertmanager receiver routing.
- Contact channel secrets.
- Collector deployment manifests.
- Managed observability vendor configuration.
- Public `/metrics` endpoint.
- write APIs, RBAC, audit write model, broker/order flow, benchmark changes, scoring changes, or DB schema changes.
