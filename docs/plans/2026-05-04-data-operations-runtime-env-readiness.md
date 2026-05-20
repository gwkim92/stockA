# Data Operations Runtime Env Readiness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a secret-free readiness gate for data operations runtime environment files before scheduler activation.

**Architecture:** A Python validator owns env group rules and emits redacted JSON. Shell scripts only render/check trusted repo-outside env files. The ingest CLI exposes the same validator so automation can call a stable command.

**Tech Stack:** Python stdlib, argparse CLI, bash verification scripts, unittest.

---

### Task 1: Validator

**Files:**
- Create: `src/stockanalysis/operations/env_readiness.py`
- Test: `tests/test_data_operations_env_readiness.py`

**Steps:**
- Define env groups and placeholder detection.
- Validate database URL or psql command presence.
- Validate FRED, Alpha Vantage, SEC identity, portfolio CSV, LLM provider, and artifact root.
- Return JSON-safe payload without secret values.

### Task 2: CLI

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Modify: `tests/test_ingest_cli.py`

**Steps:**
- Add `data-operations-env-readiness`.
- Print readiness JSON.
- Return non-zero for validation errors through existing error boundary.

### Task 3: Scripts

**Files:**
- Create: `scripts/render_data_operations_env_template.sh`
- Create: `scripts/check_data_operations_runtime_env.sh`
- Create: `scripts/verify_data_operations_runtime_env_readiness.sh`

**Steps:**
- Refuse repo-inside env file and output paths.
- Render a placeholder template with `chmod 600`.
- Source trusted env files and call the CLI.
- Verify template failure, valid env success, and no secret leakage.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/data-operations-runtime-env-readiness.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/data-operations-runtime-env-readiness/handoff.md`
- Modify: `docs/tasks/data-operations-runtime-env-readiness/review.md`

**Steps:**
- Document the activation gate.
- Move immediate next task to the next data operations slice after completion.
- Record verification evidence and residual risks.
