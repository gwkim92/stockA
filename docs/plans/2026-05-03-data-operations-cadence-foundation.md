# Data Operations Cadence Foundation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a repo-owned data operations cadence registry and connect expected recurring jobs to data-health live read status.

**Architecture:** Keep scheduling disabled and model the recurring jobs as static Python registry entries. Expose the registry through a read-only CLI report and use generated SQL values in the existing frontend data-health live query.

**Tech Stack:** Python dataclasses, stdlib CLI JSON, existing Postgres `ops.pipeline_run`, FastAPI frontend live adapter, unittest, bash verification, AWH task docs.

---

### Task 1: Create Task Docs

**Files:**

- Create: `docs/tasks/data-operations-cadence-foundation/contract.md`
- Create: `docs/tasks/data-operations-cadence-foundation/plan.md`
- Create: `docs/tasks/data-operations-cadence-foundation/handoff.md`
- Create: `docs/tasks/data-operations-cadence-foundation/review.md`

**Step 1: Define scope**

Include cadence registry, CLI report, data-health expected job status, docs, and verification.

**Step 2: Define exclusions**

Exclude scheduler activation, real credentials, deployment manifests, DB schema changes, write APIs, scoring changes, benchmark changes, and broker/order flow.

### Task 2: Add Cadence Registry

**Files:**

- Create: `src/stockanalysis/operations/__init__.py`
- Create: `src/stockanalysis/operations/cadence.py`
- Test: `tests/test_data_operations_cadence.py`

**Step 1: Add registry dataclass**

Define `DataOperationCadence` with pipeline name, cadence, domain, command template, stale threshold, artifact policy, and required env groups.

**Step 2: Add report function**

Expose `build_data_operations_cadence_report()`.

**Step 3: Add SQL values renderer**

Expose `render_data_operations_expected_jobs_sql_values()` for frontend data-health SQL.

### Task 3: Add CLI Report

**Files:**

- Modify: `src/stockanalysis/ingest/cli.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add parser command**

Add `data-operations-cadence --cadence daily|weekly|monthly`.

**Step 2: Add handler**

Print the cadence report as JSON.

### Task 4: Connect Data Health

**Files:**

- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `tests/test_frontend_live_adapter.py`
- Modify: `docs/api/frontend/examples/data-health.json`
- Modify: `apps/web/src/lib/types.ts`

**Step 1: Generate expected job CTE**

Use the cadence registry to render static `expected_jobs` values.

**Step 2: Compute health status**

Return `missing`, `failed`, `running`, `stale`, or `ok` for each expected job.

**Step 3: Preserve DTO compatibility**

Keep existing `pipeline_name`, `latest_status`, `latest_run_id`, and `finished_at` fields, then add optional operating metadata.

### Task 5: Verification And Roadmap

**Files:**

- Create: `scripts/verify_data_operations_cadence_foundation.sh`
- Create: `docs/data-operations-cadence-foundation.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `scripts/verify_frontend_api_alert_rules.sh`

**Step 1: Add verification script**

Run py_compile, targeted unittest, CLI smoke, doc checks, roadmap checks, and AGENTS next-task checks.

**Step 2: Move next task**

Set the fixed next task to `data-operations-artifact-runner`.

**Step 3: Regression**

Run:

```bash
bash scripts/verify_data_operations_cadence_foundation.sh
bash scripts/verify_project_execution_roadmap.sh
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-operations-cadence-foundation
git diff --check
```
