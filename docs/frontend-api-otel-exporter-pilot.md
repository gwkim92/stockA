# Frontend API OTLP Exporter Pilot

## Current Status

The FastAPI read-only frontend API server now has an optional OpenTelemetry/OTLP boundary.

Default mode is disabled:

```bash
STOCKANALYSIS_FRONTEND_API_OBSERVABILITY_MODE=disabled
```

Disabled mode does not import or require OpenTelemetry packages.

Opt-in OTLP mode:

```bash
STOCKANALYSIS_FRONTEND_API_OBSERVABILITY_MODE=otlp
STOCKANALYSIS_FRONTEND_API_OTLP_ENDPOINT=http://127.0.0.1:4318
```

OTLP mode requires installing the optional extra:

```bash
pip install -e ".[otel]"
```

This pilot follows the OTLP base endpoint convention: a base endpoint such as `http://collector:4318` is expanded to signal-specific paths such as `/v1/traces` and `/v1/metrics`.

References:

- OpenTelemetry OTLP exporter configuration: https://opentelemetry.io/docs/languages/sdk-configuration/otlp-exporter/
- OpenTelemetry Protocol exporter specification: https://opentelemetry.io/docs/specs/otel/protocol/exporter/
- HTTP span semantic convention: https://opentelemetry.io/docs/specs/semconv/http/http-spans/
- HTTP metric semantic convention: https://opentelemetry.io/docs/specs/semconv/http/http-metrics/

## Runtime Boundary

Environment:

- `STOCKANALYSIS_FRONTEND_API_OBSERVABILITY_MODE`: `disabled` or `otlp`; default is `disabled`.
- `STOCKANALYSIS_FRONTEND_API_OTLP_ENDPOINT`: OTLP/HTTP Collector base endpoint. Required only in `otlp` mode.

Endpoint validation:

- scheme must be `http` or `https`.
- host must be present.
- username/password are rejected.
- query string and fragment are rejected.

Public metadata:

- `/__health` exposes mode, exporter state, instrumentation state, service name, namespace, and version.
- `/__health` does not expose the OTLP endpoint.
- startup JSON does not expose the OTLP endpoint.

## Telemetry Guardrails

Access logs now include bounded fields:

- `route_template`
- `status_class`

Metric/span labels must stay low-cardinality. Use `route_template`, not raw path. Use status class or HTTP status code where appropriate. Do not use request id, raw query string, SQL text, DB URL, token, symbol, portfolio name, document id, thesis id, recommendation id, or arbitrary path segment as labels.

This follows the OpenTelemetry HTTP semantic convention that `http.route` must be a low-cardinality route template and that URI path cannot substitute for it.

## What This Does Not Do

- It does not add a public `/metrics` endpoint.
- It does not add Collector, Loki, Prometheus, Grafana, or Alertmanager deployment manifests.
- It does not configure alert receivers or secrets.
- It does not runtime-smoke a real Collector.
- It does not change DB schema, scoring, benchmark/evaluation split, auth/write boundaries, or broker/order flow.

## Next Step

The next API runtime task is `frontend-api-sql-pagination-optimization`, because response-boundary list pagination still loads full list payloads before slicing.
