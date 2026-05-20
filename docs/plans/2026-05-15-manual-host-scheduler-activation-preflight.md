# Manual Host Scheduler Activation Preflight Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a final readiness gate that checks approved exact host commands and runtime env before any external manual scheduler activation.

**Architecture:** Add a Python operations service that consumes the manual exact-command approval report and fresh runtime env readiness, then emits a secret-free preflight report. Keep shell as a thin wrapper around `stockanalysis-operations`; physical host mutation remains outside Codex.

**Tech Stack:** Python stdlib, unittest, Bash verification scripts, Agent Work Harness task docs.

---

### Task 1: Task Harness

**Files:**
- Create: `docs/tasks/manual-host-scheduler-activation-preflight/contract.md`
- Create: `docs/tasks/manual-host-scheduler-activation-preflight/plan.md`
- Create: `docs/tasks/manual-host-scheduler-activation-preflight/handoff.md`
- Create: `docs/tasks/manual-host-scheduler-activation-preflight/review.md`

**Step 1:** Record scope, mutable surface, exclusions, and verification commands.

**Step 2:** Mark actual `launchctl` and LaunchAgents writes out of scope.

### Task 2: Python Preflight Builder

**Files:**
- Create: `src/stockanalysis/operations/manual_host_scheduler_activation_preflight.py`
- Test: `tests/test_manual_host_scheduler_activation_preflight.py`

**Step 1:** Add tests for approved/pass, unapproved block, env failure block, and secret-like rejection.

**Step 2:** Implement the report builder and validation helpers.

**Step 3:** Run `PYTHONPATH=src python3 -m unittest tests.test_manual_host_scheduler_activation_preflight -v`.

### Task 3: CLI Boundary

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Modify: `tests/test_data_operations_cli.py`

**Step 1:** Add `manual-host-scheduler-activation-preflight`.

**Step 2:** Enforce repo-outside input/output with `path_policy`.

**Step 3:** Run `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli -v`.

### Task 4: Wrapper And Verification

**Files:**
- Create: `scripts/preflight_manual_host_scheduler_activation.sh`
- Create: `scripts/verify_manual_host_scheduler_activation_preflight.sh`

**Step 1:** Add thin wrapper that delegates to `stockanalysis.operations.cli`.

**Step 2:** Add a verification script that builds repo-outside fixtures and rejects missing approval, bad env, secrets, and repo-inside paths.

**Step 3:** Run `bash scripts/verify_manual_host_scheduler_activation_preflight.sh`.

### Task 5: Documentation And Roadmap

**Files:**
- Create: `docs/manual-host-scheduler-activation-preflight.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Step 1:** Document the interface, outcomes, and non-execution boundary.

**Step 2:** Keep physical activation out of Codex until the operator supplies repo-outside env/evidence and approves exact commands.

**Step 3:** Run roadmap and AWH verification.
