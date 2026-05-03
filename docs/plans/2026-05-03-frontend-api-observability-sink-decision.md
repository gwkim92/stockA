# Frontend API Observability Sink Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Decide the external observability sink boundary for the read-only FastAPI frontend API server without adding premature vendor-specific runtime dependencies.

**Architecture:** Keep app-owned observability small: request id, JSON access logs, probes, and optional OTLP egress later. Use an OpenTelemetry Collector boundary so logs, metrics, and traces can be routed to Grafana/Loki/Prometheus or a managed backend without changing application code.

**Tech Stack:** FastAPI, Uvicorn, stdout JSON logs, OpenTelemetry Collector boundary, Prometheus-compatible alerting, Grafana/Loki reference backend, shell verification scripts.

---

### Task 1: Confirm Scope

**Files:**
- Read: `docs/tasks/frontend-api-observability-sink-decision/contract.md`
- Read: `docs/frontend-api-server.md`
- Read: `docs/project-execution-roadmap.md`
- Read: `AGENTS.md`

**Step 1: Check worktree**

Run:

```bash
git status --short
```

Expected: unrelated AI retrieval docs may exist but must not be edited or staged by this task.

**Step 2: Confirm immediate task**

Run:

```bash
rg -n 'frontend-api-observability-sink-decision|현재 고정된 immediate next task' AGENTS.md docs/project-execution-roadmap.md
```

Expected: current immediate task is this task before implementation.

### Task 2: Write Decision Doc

**Files:**
- Create: `docs/frontend-api-observability-sink-decision.md`

**Step 1: Document decision**

Record:

- OpenTelemetry Collector as production telemetry egress boundary.
- stdout JSON/probes remain stable app-owned outputs.
- Grafana/Loki/Prometheus/Alertmanager as reference self-host stack.
- managed backends must be swapped behind Collector exporters, not app code.

**Step 2: Document guardrails**

Record forbidden labels:

- request id
- raw path params such as symbol, portfolio, document id, thesis id
- raw query string
- SQL text
- DB URL, token, or secret

### Task 3: Add Verification Script

**Files:**
- Create: `scripts/verify_frontend_api_observability_sink_decision.sh`
- Modify: `docs/verification-plan.md`

**Step 1: Add grep-based verification**

The script should check:

- decision doc exists.
- OpenTelemetry Collector, OTLP, Loki, Prometheus, Alertmanager, high-cardinality guardrail are documented.
- AGENTS and roadmap moved the next task to `frontend-api-otel-exporter-pilot`.
- task handoff/review exists.

**Step 2: Run verification**

Run:

```bash
bash scripts/verify_frontend_api_observability_sink_decision.sh
```

Expected: PASS.

### Task 4: Update Roadmap And Handoff

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `docs/frontend-api-server.md`
- Modify: `docs/frontend-architecture.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/frontend-api-observability-sink-decision/handoff.md`
- Modify: `docs/tasks/frontend-api-observability-sink-decision/review.md`

**Step 1: Move immediate next task**

Set next task to `frontend-api-otel-exporter-pilot`.

**Step 2: Record verification evidence**

Run:

```bash
bash scripts/verify_project_execution_roadmap.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-api-observability-sink-decision
git diff --check
```

Expected: all pass.
