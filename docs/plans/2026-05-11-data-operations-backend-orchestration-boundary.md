# Data Operations Backend Orchestration Boundary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move data operations orchestration entrypoints toward a Python backend CLI/service boundary so shell scripts stop owning product logic.

**Architecture:** Keep FastAPI read-only for frontend DTOs. Add a `stockanalysis-operations` CLI backed by `src/stockanalysis/operations/` service modules, and keep shell as verification or thin wrapper entrypoints only.

**Tech Stack:** Python argparse, stdlib JSON/path handling, existing unittest harness, existing shell verification scripts.

---

### Task 1: Document The Boundary Correction

**Files:**
- Create: `docs/tasks/data-operations-backend-orchestration-boundary/contract.md`
- Create: `docs/tasks/data-operations-backend-orchestration-boundary/plan.md`
- Create: `docs/tasks/data-operations-backend-orchestration-boundary/handoff.md`
- Create: `docs/tasks/data-operations-backend-orchestration-boundary/review.md`

**Steps:**
- Write the contract before code changes.
- State why this task is interposed before execution final preflight.
- Explicitly exclude FastAPI write APIs, host scheduler mutation, schema changes, and broker/order flow.

### Task 2: Add Operations CLI Boundary

**Files:**
- Create: `src/stockanalysis/operations/cli.py`
- Modify: `pyproject.toml`

**Steps:**
- Add `stockanalysis-operations = "stockanalysis.operations.cli:main_entry"`.
- Implement `cadence`, `run`, `env-readiness`, and `host-activation-execution-decision`.
- Preserve old `stockanalysis-ingest data-operations-*` compatibility for now.

### Task 3: Move Shared Wrapper Policy Into Python

**Files:**
- Create: `src/stockanalysis/operations/path_policy.py`
- Create: `src/stockanalysis/operations/report_io.py`
- Test: `tests/test_data_operations_cli.py`

**Steps:**
- Implement repo-outside path validation in Python.
- Implement JSON object load/write helpers.
- Add tests that prove repo-inside execution request paths are rejected by Python policy.

### Task 4: Thin A Representative Wrapper

**Files:**
- Modify: `scripts/decide_data_operations_live_scheduler_host_activation_execution.sh`
- Modify: `scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh`

**Steps:**
- Replace shell path parsing and Python heredoc with `python -m stockanalysis.operations.cli host-activation-execution-decision`.
- Keep wrapper executable.
- Extend verification to compile/test the new CLI and helpers.

### Task 5: Update Roadmap And Verification

**Files:**
- Create: `docs/data-operations-backend-orchestration-boundary.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Steps:**
- Record the boundary task as implemented.
- Keep immediate next task as execution final preflight after this correction.
- State that future final preflight should use `stockanalysis-operations`.

### Task 6: Verify

**Commands:**
- `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli -v`
- `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `git diff --check`
