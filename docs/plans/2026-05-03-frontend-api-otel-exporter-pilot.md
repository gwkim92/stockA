# Frontend API OTLP Exporter Pilot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an optional OTLP exporter pilot boundary to the FastAPI read-only frontend API server while keeping default runtime dependency-free.

**Architecture:** Keep `disabled` as the default observability mode. Add a small internal config/runtime module that validates OTLP settings, redacts endpoint metadata, and only imports OpenTelemetry packages when `otlp` mode is explicitly enabled.

**Tech Stack:** Python 3.11, FastAPI, optional OpenTelemetry Python packages, OTLP/HTTP, `unittest`, shell verification scripts.

---

### Task 1: Define Observability Config

**Files:**
- Create: `src/stockanalysis/frontend/observability.py`
- Test: `tests/test_frontend_observability.py`

**Step 1: Write config tests**

Cover:

- default mode is disabled.
- `otlp` requires an endpoint.
- endpoint must be `http` or `https`.
- endpoint with userinfo/query/fragment is rejected.
- public metadata does not expose endpoint.

**Step 2: Implement minimal config**

Create dataclasses and validation helpers. Do not import OpenTelemetry at module import time.

### Task 2: Wire API Server

**Files:**
- Modify: `src/stockanalysis/frontend/api_server.py`
- Modify: `tests/test_frontend_api_server.py`

**Step 1: Add app parameters and CLI flags**

Add:

- `observability_mode`
- `otlp_endpoint`
- `--observability-mode`
- `--otlp-endpoint`

**Step 2: Add safe metadata**

Expose mode and configured boolean in `/__health`; do not expose endpoint.

**Step 3: Add route template access log field**

Log `route_template` and `status_class`, not raw query.

### Task 3: Optional Dependency Extra

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add optional dependency group**

Add `[project.optional-dependencies]` with an `otel` extra for:

- `opentelemetry-api`
- `opentelemetry-sdk`
- `opentelemetry-exporter-otlp-proto-http`
- `opentelemetry-instrumentation-fastapi`

Base dependencies must not require OTel.

### Task 4: Verification And Docs

**Files:**
- Create: `docs/frontend-api-otel-exporter-pilot.md`
- Create: `scripts/verify_frontend_api_otel_exporter_pilot.sh`
- Modify: `docs/frontend-api-server.md`
- Modify: `docs/frontend-api-observability-sink-decision.md`
- Modify: `docs/frontend-architecture.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Step 1: Add verification script**

Run targeted tests and grep for docs/metadata guardrails.

**Step 2: Move next task**

Move immediate next task to SQL-level pagination optimization.

**Step 3: Run full verification**

Run:

```bash
bash scripts/verify_frontend_api_otel_exporter_pilot.sh
bash scripts/verify_project_execution_roadmap.sh
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-otel-exporter-pilot
git diff --check
```
