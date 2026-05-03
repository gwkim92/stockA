# Implementation Plan

1. Create task contract, handoff, review, and standalone plan.
2. Add `src/stockanalysis/frontend/observability.py` with `disabled|otlp` config parsing and safe endpoint validation.
3. Add optional OTel dependency extra in `pyproject.toml` without making base install require OTel.
4. Wire `create_app()` and CLI args to observability config.
5. Keep default disabled mode no-op and expose only safe public metadata.
6. Add tests for disabled mode, invalid endpoint, missing optional packages, route template metadata, and no endpoint leakage.
7. Add verification script and update roadmap/AGENTS to the next task.
8. Run targeted and regression verification and record evidence.

## Future Implementation Sequence

1. Run `pip install -e ".[otel]"` in a dedicated environment.
2. Add a local Collector smoke task with a repo-safe sample config only if deployment boundary allows it.
3. Add alert rule examples after request metrics are collected in a real backend.
4. Tune latency/error thresholds from observed production traffic.

## Do Not Do In This Task

- Do not add receiver secrets.
- Do not add deployment manifests.
- Do not add a public `/metrics` endpoint.
- Do not label metrics with request id, raw path/query, SQL text, DB URL, token, symbol, or portfolio.
