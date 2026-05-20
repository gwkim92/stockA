# Data Operations Scheduler Activation Boundary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a generic data operations scheduler wrapper boundary without installing or enabling any scheduler.

**Architecture:** A Python helper builds secret-free preflight and skip reports from the cadence registry. A shell wrapper composes env readiness, preflight, optional skip, and `data-operations-run`. Verification uses temp repo-outside env and artifacts and asserts no host scheduler artifact exists.

**Tech Stack:** Python stdlib, bash, unittest.

---

### Task 1: Scheduler Boundary Helper

**Files:**
- Create: `src/stockanalysis/operations/scheduler_boundary.py`
- Test: `tests/test_data_operations_scheduler_boundary.py`

**Steps:**
- Build preflight report for known cadence job.
- Validate ISO run date and skip dates.
- Redact command argv.
- Build skip report.

### Task 2: Scheduler Wrapper

**Files:**
- Create: `scripts/run_data_operations_scheduler_job.sh`

**Steps:**
- Parse env file, job id, timeout, run date, skip dates, and command.
- Refuse repo-inside env files.
- Run env readiness before execution.
- Support `--preflight-only`.
- Emit skip JSON artifact on configured skip date.
- Invoke `data-operations-run` for non-skip execution.

### Task 3: Verification

**Files:**
- Create: `scripts/verify_data_operations_scheduler_activation_boundary.sh`

**Steps:**
- Check script syntax and targeted tests.
- Verify missing/repo-inside env rejection.
- Verify preflight redaction.
- Verify skip artifact.
- Verify non-skip artifact runner invocation.
- Verify no cron/launchd/GitHub Actions scheduler activation artifacts exist.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/data-operations-scheduler-activation-boundary.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: task handoff/review.

**Steps:**
- Document the scheduler boundary.
- Move immediate next task after completion.
- Record verification evidence and residual risks.
