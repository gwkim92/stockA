# Frontend API Observability Sink Decision

## Decision

Production telemetry egress for the read-only FastAPI frontend API server will use an OpenTelemetry Collector boundary.

The application keeps its current app-owned observability outputs:

- `X-Request-ID` response header.
- JSON access logs on stdout through `stockanalysis.frontend.api_server`.
- `/__live`, `/__health`, and `/__ready` probes.
- stable error envelopes with request id.

The follow-up `frontend-api-otel-exporter-pilot` added optional OTLP export behind an env flag, with default mode disabled.

## Reference Stack

Reference self-host profile:

- logs: Loki or a Loki-compatible backend.
- metrics: Prometheus-compatible metrics backend.
- alerting: Prometheus alert rules routed through Alertmanager.
- dashboards: Grafana.
- collection and export boundary: OpenTelemetry Collector.

Managed observability vendors are allowed only behind Collector exporters. Application code must not depend directly on a vendor SDK or vendor-specific endpoint.

This follows the OpenTelemetry Collector goal of vendor-agnostic telemetry collection/export and avoids maintaining multiple app-specific agents. Prometheus alerting remains a two-layer model: alert rules detect conditions, Alertmanager groups/routes/silences notifications. Loki labels must stay low-cardinality; request ids and other unbounded identifiers must remain log fields or structured metadata, not index labels.

References:

- OpenTelemetry Collector: https://opentelemetry.io/docs/collector/
- Prometheus alerting overview: https://prometheus.io/docs/alerting/latest/overview/
- Prometheus Alertmanager: https://prometheus.io/docs/alerting/latest/alertmanager/
- Grafana Loki label best practices: https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/
- Grafana Loki OpenTelemetry ingestion: https://grafana.com/docs/loki/latest/send-data/otel/

## Telemetry Contract

Allowed resource attributes:

- `service.name=stockanalysis-frontend-api`
- `service.namespace=stockanalysis`
- `deployment.environment.name`
- `service.version`
- `service.instance.id`

Allowed log fields:

- `timestamp`
- `level`
- `logger`
- `request_id`
- `method`
- `path`
- `route_template`
- `status`
- `duration_ms`
- `profile`
- `source_mode`
- `error_code`

Allowed metric labels:

- `route_template`
- `method`
- `status_class`
- `profile`
- `source_mode`
- `error_code`

Forbidden labels:

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

These values may appear as log fields only when they are already safe and useful for debugging. They must not become metric labels or Loki labels.

## Initial Metrics

The OTLP pilot should start with bounded request/runtime metrics only:

- `frontend_api_requests_total`
- `frontend_api_request_duration_seconds`
- `frontend_api_request_timeouts_total`
- `frontend_api_adapter_errors_total`
- `frontend_api_ready`
- `frontend_api_db_pool_ready`

Do not emit investment symbols, portfolio names, thesis ids, SQL text, raw query strings, tokens, or DB URLs as labels.

## Initial Alerts

First alert candidates:

- `FrontendApiDown`: `/__live` or process scrape unavailable for 5 minutes.
- `FrontendApiNotReady`: `/__ready` fails for 5 minutes.
- `FrontendApiHigh5xxRate`: 5xx ratio above threshold for 10 minutes.
- `FrontendApiTimeoutSpike`: timeout count above threshold for 10 minutes.
- `FrontendApiHighLatency`: p95 request latency above threshold for 10 minutes.
- `FrontendApiAdapterErrorSpike`: adapter error count above threshold for 10 minutes.

Alert receiver destination is not stored in this repository. Slack, email, PagerDuty, OpsGenie, GitHub issue creation, or another receiver must be configured in deployment secrets or operator-owned infrastructure.

## Rejected Alternatives

Vendor direct SDK in app:

- rejected for now because it couples application code to a commercial backend and increases secret/config surface.

Public `/metrics` endpoint now:

- rejected for now because scrape network policy and auth boundary are not defined.

Loki direct client in app:

- rejected for now because stdout JSON already exists and Collector/agent ingestion can preserve platform portability.

Full Grafana/Loki/Prometheus deployment manifests now:

- rejected for now because deployment topology is intentionally repo-outside until an environment is selected.

Trace-first instrumentation:

- deferred. Request metrics and log shipping are more immediately useful for this read-only API server. Traces can follow once OTLP exporter mode exists.

## Implementation Boundary

`frontend-api-otel-exporter-pilot` should:

- add optional OTel dependencies only if tests prove disabled mode has no runtime requirement. Implemented.
- support `STOCKANALYSIS_FRONTEND_API_OBSERVABILITY_MODE=disabled|otlp`. Implemented.
- support `STOCKANALYSIS_FRONTEND_API_OTLP_ENDPOINT`. Implemented.
- preserve existing stdout JSON logs. Implemented.
- avoid emitting high-cardinality labels. Implemented with bounded `route_template` and `status_class` fields.
- avoid exposing new public endpoints. Implemented.
- include unit tests for disabled mode, OTLP config validation, and safe attribute naming. Implemented.

It must not add write APIs, RBAC, audit write model, DB schema changes, scoring changes, benchmark/evaluation changes, broker/order flow, or real alert receiver secrets.
