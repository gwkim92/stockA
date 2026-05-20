# Data Operations Runtime Smoke Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Prove one representative data operations cadence job can pass env readiness and run through artifact capture against a disposable local DB before scheduler activation.

**Architecture:** A shell wrapper composes the existing env readiness checker and data operations artifact runner. A tiny Python report builder validates the two JSON payloads and emits a secret-free smoke summary. Verification starts a disposable Postgres container, applies migrations/seeds, creates a repo-outside temp env, and runs fixture-backed `macro-batch-upsert`.

**Tech Stack:** Python stdlib, bash, Docker Postgres, unittest.

---

### Task 1: Smoke Report Builder

**Files:**
- Create: `src/stockanalysis/operations/runtime_smoke.py`
- Test: `tests/test_data_operations_runtime_smoke.py`

**Steps:**
- Validate readiness payload is passed.
- Validate artifact run payload exists.
- Emit secret-free smoke summary.
- Fail when readiness or artifact run status is not passed/succeeded.

### Task 2: Smoke Wrapper

**Files:**
- Create: `scripts/smoke_data_operations_runtime.sh`

**Steps:**
- Parse `--env-file`, `--job-id`, `--timeout-seconds`, and command after `--`.
- Refuse missing command.
- Run `scripts/check_data_operations_runtime_env.sh`.
- Source the trusted env file and run `stockanalysis-ingest data-operations-run`.
- Combine readiness and artifact metadata into one JSON summary.

### Task 3: Verification

**Files:**
- Create: `scripts/verify_data_operations_runtime_smoke.sh`

**Steps:**
- Start Docker Postgres.
- Apply migrations and seeds.
- Create repo-outside temp env and portfolio CSV.
- Run the smoke wrapper for `macro-weekly` with fixture `macro-batch-upsert`.
- Assert stdout/stderr/metadata artifacts and DB rows exist.
- Assert no secret-like values leak in smoke JSON or metadata.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/data-operations-runtime-smoke.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/data-operations-runtime-smoke/handoff.md`
- Modify: `docs/tasks/data-operations-runtime-smoke/review.md`

**Steps:**
- Document the smoke boundary.
- Move immediate next task after completion.
- Record verification evidence and residual risks.
