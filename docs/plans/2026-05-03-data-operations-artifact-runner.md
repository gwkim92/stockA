# Data Operations Artifact Runner Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a generic repo-local runner that captures stdout, stderr, and metadata artifacts for one known data operations cadence job.

**Architecture:** Reuse the cadence registry for job validation. Keep scheduler activation out of scope and expose a simple Python function plus `stockanalysis-ingest data-operations-run` CLI.

**Tech Stack:** Python subprocess, stdlib JSON/path/tempfile, existing ingest CLI, unittest, bash verification, AWH task docs.

---

### Task 1: Create Task Docs

**Files:**

- Create: `docs/tasks/data-operations-artifact-runner/contract.md`
- Create: `docs/tasks/data-operations-artifact-runner/plan.md`
- Create: `docs/tasks/data-operations-artifact-runner/handoff.md`
- Create: `docs/tasks/data-operations-artifact-runner/review.md`

**Step 1: Define scope**

Include known job validation, artifact directory creation, stdout/stderr/metadata capture, CLI, docs, and verification.

**Step 2: Define exclusions**

Exclude scheduler activation, production env files, real credentials, DB schema changes, write APIs, RBAC, scoring, benchmark changes, and broker/order flow.

### Task 2: Add Runner Module

**Files:**

- Create: `src/stockanalysis/operations/artifact_runner.py`
- Modify: `src/stockanalysis/operations/cadence.py`
- Test: `tests/test_data_operations_artifact_runner.py`

**Step 1: Add job lookup**

Add `get_data_operation_cadence(job_id)`.

**Step 2: Add run function**

Implement `run_data_operation_artifact_command()` with artifact root resolution, subprocess execution, stdout/stderr write, optional stdout JSON write, metadata write, and timeout support.

**Step 3: Add redaction**

Redact sensitive argv values before metadata persistence.

### Task 3: Add CLI

**Files:**

- Modify: `src/stockanalysis/ingest/cli.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add parser**

Add `data-operations-run --job-id <id> [--artifact-root <path>] [--timeout-seconds N] -- <command...>`.

**Step 2: Add handler**

Print metadata JSON and return the child exit code.

### Task 4: Docs And Roadmap

**Files:**

- Create: `docs/data-operations-artifact-runner.md`
- Create: `scripts/verify_data_operations_artifact_runner.sh`
- Modify: `docs/data-operations-cadence-foundation.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `scripts/verify_data_operations_cadence_foundation.sh`

**Step 1: Add verification script**

Run py_compile, unit tests, CLI smoke, doc checks, and next-task checks.

**Step 2: Move next task**

Set fixed next task to `data-operations-runtime-env-readiness`.

### Task 5: Regression

Run:

```bash
bash scripts/verify_data_operations_artifact_runner.sh
bash scripts/verify_data_operations_cadence_foundation.sh
bash scripts/verify_project_execution_roadmap.sh
PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task data-operations-artifact-runner
git diff --check
```
