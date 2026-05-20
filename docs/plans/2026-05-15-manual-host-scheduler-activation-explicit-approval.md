# Manual Host Scheduler Activation Explicit Approval Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a safe exact-command approval packet for manual host scheduler activation without executing host mutation.

**Architecture:** Add a Python operations service that consumes the confirmed host activation execution report, validates optional approval records, and emits a secret-free approval gate report. Keep shell as a thin wrapper around `stockanalysis-operations`; all physical host mutation remains outside Codex.

**Tech Stack:** Python stdlib, unittest, Bash verification scripts, Agent Work Harness task docs.

---

### Task 1: Task Harness

**Files:**
- Create: `docs/tasks/manual-host-scheduler-activation-explicit-approval/contract.md`
- Create: `docs/tasks/manual-host-scheduler-activation-explicit-approval/plan.md`
- Create: `docs/tasks/manual-host-scheduler-activation-explicit-approval/handoff.md`
- Create: `docs/tasks/manual-host-scheduler-activation-explicit-approval/review.md`

**Step 1:** Record scope, mutable surface, exclusions, and verification commands.

**Step 2:** Mark actual `launchctl` and LaunchAgents writes out of scope.

### Task 2: Python Approval Builder

**Files:**
- Create: `src/stockanalysis/operations/manual_host_scheduler_activation_approval.py`
- Test: `tests/test_manual_host_scheduler_activation_approval.py`

**Step 1:** Add tests for missing approval, approval, abort, command drift, and secret-like rejection.

**Step 2:** Implement the report builder and validation helpers.

**Step 3:** Run `PYTHONPATH=src python3 -m unittest tests.test_manual_host_scheduler_activation_approval -v`.

### Task 3: CLI Boundary

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Modify: `tests/test_data_operations_cli.py`

**Step 1:** Add `manual-host-scheduler-activation-explicit-approval`.

**Step 2:** Enforce repo-outside input/output with `path_policy`.

**Step 3:** Run `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli -v`.

### Task 4: Wrapper And Verification

**Files:**
- Create: `scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh`
- Create: `scripts/verify_manual_host_scheduler_activation_explicit_approval.sh`

**Step 1:** Add thin wrapper that delegates to `stockanalysis.operations.cli`.

**Step 2:** Add a verification script that builds repo-outside fixtures and rejects command drift, secrets, and repo-inside paths.

**Step 3:** Run `bash scripts/verify_manual_host_scheduler_activation_explicit_approval.sh`.

### Task 5: Documentation And Roadmap

**Files:**
- Create: `docs/manual-host-scheduler-activation-explicit-approval.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Step 1:** Document the interface, record shape, outcomes, and non-execution boundary.

**Step 2:** Keep current immediate next at `manual-host-scheduler-activation-explicit-approval` until exact external approval and physical mutation happen.

**Step 3:** Run roadmap and AWH verification.
