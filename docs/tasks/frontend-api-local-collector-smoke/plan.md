# Implementation Plan

1. Add task contract, implementation plan, handoff, and review placeholders.
2. Add `scripts/smoke_frontend_api_local_otlp_receiver.py` that starts a local OTLP/HTTP receiver on a random loopback port.
3. In the smoke helper, start the FastAPI frontend API server on a random loopback port with `--observability-mode otlp` and the local receiver endpoint.
4. Hit `/__health` and one API route, assert safe metadata and successful frontend API response.
5. Wait for at least one `/v1/traces` POST and fail clearly if optional OpenTelemetry packages are missing.
6. Add `scripts/verify_frontend_api_local_collector_smoke.sh`.
7. Add docs and update roadmap/verification/README/AGENTS next task.
8. Run targeted smoke with an OTEL-enabled Python env and record evidence.
