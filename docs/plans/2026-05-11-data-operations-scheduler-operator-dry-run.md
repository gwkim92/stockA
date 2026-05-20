# Data Operations Scheduler Operator Dry Run Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rehearse the Data Operations scheduler activation runbook without mutating host scheduler state.

**Architecture:** A Bash wrapper orchestrates existing readiness, scheduler preflight, install dry-run, and alert validation scripts. A small Python report builder validates those outputs and emits a secret-free evidence report.

**Tech Stack:** Python stdlib, Bash, existing Agent Work Harness task docs.

---

### Task 1: Report Builder

**Files:**
- Create: `src/stockanalysis/operations/scheduler_operator_dry_run.py`
- Create: `tests/test_data_operations_scheduler_operator_dry_run.py`

**Steps:**

1. Add `build_data_operations_scheduler_operator_dry_run_report`.
2. Validate readiness passed.
3. Validate scheduler preflight passed and activation is boundary-only.
4. Validate install manifest is dry-run and host install path was not written.
5. Validate alert rule output exists.
6. Return a secret-free report with evidence paths and blocked host activation state.
7. Unit test success and failure paths.

### Task 2: Wrapper Script

**Files:**
- Create: `scripts/dry_run_data_operations_scheduler_operator_flow.sh`

**Steps:**

1. Parse `--env-file`, `--job-id`, `--output-dir`, `--timeout-seconds`, `--run-date`, and command after `--`.
2. Refuse repo-inside env/output paths.
3. Write readiness, preflight, render, alert validation, and final report artifacts under output dir.
4. Never run `launchctl`.
5. Never execute the child data operation command.

### Task 3: Verification Script

**Files:**
- Create: `scripts/verify_data_operations_scheduler_operator_dry_run.sh`

**Steps:**

1. Create a temporary repo-outside env file, positions CSV, artifact root, and output dir.
2. Run the wrapper against `macro-weekly` with fixture command argv.
3. Assert expected evidence files exist.
4. Assert report has `operator_dry_run=passed`, `scheduler_activation=not_installed`, `launchctl_executed=false`.
5. Assert fake secret values do not leak into the final report.
6. Assert docs/roadmap/AGENTS/AWH markers.

### Task 4: Docs And Roadmap

**Files:**
- Create: `docs/data-operations-scheduler-operator-dry-run.md`
- Modify: `docs/data-operations-scheduler-activation-runbook.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: prior data-operations verification scripts

**Steps:**

1. Document the dry-run interface and evidence bundle.
2. Mark `data-operations-scheduler-operator-dry-run` complete in roadmap.
3. Move immediate next task to `data-operations-scheduler-activation-approval-gate`.
4. Update handoff/review after verification.

### Task 5: Verification

**Commands:**

```bash
bash scripts/verify_data_operations_scheduler_operator_dry_run.sh
bash scripts/verify_data_operations_scheduler_activation_runbook.sh
bash scripts/verify_project_execution_roadmap.sh
/tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests
git diff --check
```
