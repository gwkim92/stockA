# Frontend API Local Collector Smoke

Date: 2026-05-03

## What This Proves

The FastAPI read-only frontend API server can run in `otlp` observability mode and send real OTLP/HTTP telemetry to a local receiver.

The smoke starts:

- a local OTLP-compatible HTTP receiver on loopback.
- a frontend API server subprocess on a random loopback port.
- one health request and one frontend API read request.

The smoke passes only if:

- `/__health` reports `observability_mode=otlp`.
- `/__health` reports `instrumented=true`.
- startup and health metadata do not expose the OTLP endpoint.
- the local receiver captures at least one `/v1/traces` POST.

## Command

Run with a Python environment that has `stockanalysis[otel]` installed:

```bash
PYTHON_BIN=/path/to/otel-enabled-python bash scripts/verify_frontend_api_local_collector_smoke.sh
```

The default FastAPI verification venv intentionally does not install the optional OTel extra, so this smoke should use an isolated OTel-enabled venv.

## Boundary

This smoke uses a deterministic local OTLP receiver rather than adding Collector/Loki/Prometheus/Grafana deployment manifests. It verifies app-to-OTLP egress without committing production secrets or choosing an alert receiver.

## Not Included

- no public `/metrics` endpoint.
- no Collector deployment manifest.
- no Loki/Prometheus/Grafana/Alertmanager deployment.
- no alert receiver secret.
- no DB schema/scoring/benchmark/evaluation split change.
- no auth/RBAC/write API.
- no broker/order flow.

## Follow-Up

`frontend-api-alert-rules` adds the first secret-free frontend API alert rule references.

Receiver routing, managed Collector deployment, and production contact channels remain outside this public repository.
