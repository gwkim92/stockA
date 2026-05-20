# Frontend API Local Collector Smoke Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a deterministic local OTLP smoke for the FastAPI read-only frontend API server.

**Architecture:** A Python smoke helper starts a local OTLP/HTTP receiver and a frontend API server subprocess in `otlp` mode. The helper performs a health/API request, verifies safe metadata, and waits until the receiver captures at least one `/v1/traces` POST.

**Tech Stack:** Python stdlib `http.server`, subprocess-managed FastAPI/Uvicorn server, OpenTelemetry optional extra `stockanalysis[otel]`, shell verification script.

---

### Task 1: Task Docs

**Files:**
- Create: `docs/tasks/frontend-api-local-collector-smoke/contract.md`
- Create: `docs/tasks/frontend-api-local-collector-smoke/plan.md`
- Create: `docs/tasks/frontend-api-local-collector-smoke/handoff.md`
- Create: `docs/tasks/frontend-api-local-collector-smoke/review.md`

**Steps:**
1. Create the task contract and guardrails.
2. Record that this is an OTLP-compatible local receiver smoke, not full Collector deployment.
3. Record required verification commands.

### Task 2: Smoke Helper

**Files:**
- Create: `scripts/smoke_frontend_api_local_otlp_receiver.py`

**Steps:**
1. Write an OTLP receiver using `ThreadingHTTPServer`.
2. Start frontend API server subprocess with `--observability-mode otlp`.
3. Poll `/__health` until ready.
4. Call `/api/dashboard/today`.
5. Wait until `/v1/traces` POST arrives.
6. Print JSON summary.

### Task 3: Verification Script

**Files:**
- Create: `scripts/verify_frontend_api_local_collector_smoke.sh`

**Steps:**
1. Compile the smoke helper.
2. Run focused observability/API server unit tests.
3. Run the smoke helper.
4. Assert docs and roadmap markers.

### Task 4: Docs And Roadmap

**Files:**
- Create: `docs/frontend-api-local-collector-smoke.md`
- Modify: `docs/frontend-api-otel-exporter-pilot.md`
- Modify: `docs/frontend-api-observability-sink-decision.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Steps:**
1. Document what the local smoke proves and does not prove.
2. Move the fixed immediate next task to `frontend-api-alert-rules`.
3. Add verification-plan entry.

### Task 5: Verification

**Commands:**
- `python3 -m py_compile scripts/smoke_frontend_api_local_otlp_receiver.py`
- `PYTHON_BIN=<python-with-stockanalysis-otel-extra> bash scripts/verify_frontend_api_local_collector_smoke.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-local-collector-smoke`
- `git diff --check`
