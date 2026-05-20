# Data Operations Host Activation Execution Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a host activation execution gate that validates final preflight and explicit confirmation without running host mutation inside this task.

**Architecture:** Keep execution logic in `src/stockanalysis/operations/` and expose it through `stockanalysis-operations`. Shell remains a thin wrapper; physical host mutation remains outside this task.

**Tech Stack:** Python argparse, existing operations modules, unittest, shell verification harness.

---

### Task 1: Contract And Boundary

**Files:**
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution/contract.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution/plan.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution/handoff.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution/review.md`

**Steps:**
- Document that this task cannot run `launchctl`.
- Document that manual host command execution remains separate and high risk.

### Task 2: Service And CLI

**Files:**
- Create: `src/stockanalysis/operations/scheduler_activation_execution.py`
- Modify: `src/stockanalysis/operations/cli.py`

**Steps:**
- Validate execution final preflight report.
- Validate optional confirmation record.
- Output blocked, aborted, or confirmed-for-manual-operator report without executing commands.

### Task 3: Wrapper And Tests

**Files:**
- Create: `scripts/run_data_operations_live_scheduler_host_activation_execution.sh`
- Create: `tests/test_data_operations_scheduler_activation_execution.py`

**Steps:**
- Keep wrapper thin.
- Test missing confirmation, confirm, abort, invalid final preflight, mismatched confirmation path, and secret-like values.

### Task 4: Verification And Docs

**Files:**
- Create: `scripts/verify_data_operations_live_scheduler_host_activation_execution.sh`
- Create: `docs/data-operations-live-scheduler-host-activation-execution.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Steps:**
- Verify repo-outside final preflight evidence and confirmation records.
- Verify no `launchctl` execution or host LaunchAgents writes.
- Record that next action is manual/explicit host command approval, not automatic Codex execution.

### Task 5: Run Checks

**Commands:**
- `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_execution -v`
- `bash scripts/verify_data_operations_live_scheduler_host_activation_execution.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests`
- `git diff --check`
