# Data Operations Host Activation Execution Final Preflight Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Revalidate approved host activation execution evidence and fresh runtime readiness immediately before any separate host mutation task.

**Architecture:** Add a Python operations service report builder and expose it through `stockanalysis-operations`. Keep shell as a thin wrapper and keep actual host mutation out of scope.

**Tech Stack:** Python argparse, existing operations modules, stdlib env parsing, unittest, existing shell verification harness.

---

### Task 1: Contract And Boundary

**Files:**
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/contract.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/plan.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/handoff.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-final-preflight/review.md`

**Steps:**
- Document that this task cannot run `launchctl`.
- Document that the next actual execution task remains high-risk and requires explicit confirmation.

### Task 2: Service And CLI

**Files:**
- Create: `src/stockanalysis/operations/env_file.py`
- Create: `src/stockanalysis/operations/scheduler_activation_execution_final_preflight.py`
- Modify: `src/stockanalysis/operations/cli.py`

**Steps:**
- Load trusted repo-outside env files in Python.
- Build pass/block reports for execution final preflight.
- Add `stockanalysis-operations host-activation-execution-final-preflight`.

### Task 3: Wrapper And Tests

**Files:**
- Create: `scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh`
- Create: `tests/test_data_operations_scheduler_activation_execution_final_preflight.py`
- Modify: `tests/test_data_operations_cli.py`

**Steps:**
- Keep wrapper thin.
- Test approved pass, denied block, runtime block, path mismatch, command preview drift, secret rejection, env parser behavior.

### Task 4: Verification And Docs

**Files:**
- Create: `scripts/verify_data_operations_live_scheduler_host_activation_execution_final_preflight.sh`
- Create: `docs/data-operations-live-scheduler-host-activation-execution-final-preflight.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Steps:**
- Verify repo-outside evidence chain.
- Verify no launchctl execution or host LaunchAgents writes.
- Update immediate next task to a separate host activation execution task.

### Task 5: Run Checks

**Commands:**
- `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_execution_final_preflight tests.test_data_operations_cli -v`
- `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_final_preflight.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests`
- `git diff --check`
