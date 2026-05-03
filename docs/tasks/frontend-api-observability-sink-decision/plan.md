# Implementation Plan

1. Create task contract and keep scope decision-only.
2. Document the selected observability egress boundary.
3. Define allowed telemetry attributes, labels, and forbidden high-cardinality fields.
4. Define first alert candidates and receiver boundary without adding secrets.
5. Add verification script that checks decision doc, roadmap, README, AGENTS, and task docs.
6. Update handoff/review with verification evidence and next implementation task.

## Future Implementation Sequence

1. Create `frontend-api-otel-exporter-pilot` task contract.
2. Add optional OpenTelemetry dependencies and keep default mode disabled.
3. Emit bounded request metrics and spans through OTLP only when configured.
4. Verify no DB URL, token, raw query, SQL text, request id label, symbol, or portfolio id becomes a metric/log label.
5. Add local collector config only after deployment boundary accepts repo-owned sample config.
6. Add alert rules after there is a scrape or OTLP metrics smoke.

## Do Not Do In This Task

- Do not add OTel SDK dependencies.
- Do not create `/metrics`.
- Do not add Grafana/Loki/Prometheus deployment manifests.
- Do not add alert receiver secrets.
- Do not change frontend DTOs, DB schema, scoring, benchmark, or auth/write boundaries.
