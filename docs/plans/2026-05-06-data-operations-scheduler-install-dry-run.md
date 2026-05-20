# Data Operations Scheduler Install Dry Run Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Render a host scheduler artifact for data operations in dry-run mode without installing or activating it.

**Architecture:** A Python helper builds launchd plist payloads and a secret-free manifest from the cadence registry. A shell wrapper validates repo-outside paths and writes plist/manifest to a caller-provided output directory. Verification inspects plist contents and asserts no host scheduler path is written.

**Tech Stack:** Python stdlib `plistlib`, bash, unittest.

---

### Task 1: Renderer Helper

**Files:**
- Create: `src/stockanalysis/operations/scheduler_install.py`
- Test: `tests/test_data_operations_scheduler_install.py`

**Steps:**
- Derive daily/weekly launchd schedule from cadence.
- Build plist payload calling `run_data_operations_scheduler_job.sh`.
- Build dry-run manifest.
- Reject monthly first-business-day jobs.

### Task 2: Render Script

**Files:**
- Create: `scripts/render_data_operations_scheduler_install.sh`

**Steps:**
- Parse `--output-dir`, `--env-file`, `--job-id`, optional `--label`, `--timeout-seconds`, and command after `--`.
- Refuse repo-inside env/output paths.
- Write plist and manifest.
- Print manifest path.

### Task 3: Verification

**Files:**
- Create: `scripts/verify_data_operations_scheduler_install_dry_run.sh`

**Steps:**
- Run targeted tests.
- Render `macro-weekly` plist/manifest to temp output.
- Inspect plist schedule and program args.
- Confirm manifest is secret-free.
- Confirm monthly job rejection.
- Confirm no host scheduler path is written.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/data-operations-scheduler-install-dry-run.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: task handoff/review.

**Steps:**
- Document the dry-run install boundary.
- Move immediate next task after completion.
- Record verification evidence and residual risks.
