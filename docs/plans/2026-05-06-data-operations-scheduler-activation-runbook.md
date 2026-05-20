# Data Operations Scheduler Activation Runbook Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Define the manual activation, rollback, disable, and evidence runbook required before enabling recurring Data Operations scheduler jobs.

**Architecture:** This is an operations-boundary slice. It adds a runbook and verification script only; host scheduler mutation remains a future explicitly approved action.

**Tech Stack:** Bash verification, markdown task documentation, existing Agent Work Harness task contract.

---

### Task 1: Runbook Document

**Files:**
- Create: `docs/data-operations-scheduler-activation-runbook.md`

**Steps:**

1. Document activation boundary and non-goals.
2. List required inputs, including repo-outside env file, artifact root, rendered plist, manifest, alert rules, and operator approval.
3. Document stop conditions that block activation.
4. Document preflight and install dry-run commands.
5. Document launchd activation commands as reference only.
6. Document rollback, disable, and evidence checklist.

### Task 2: Verification Script

**Files:**
- Create: `scripts/verify_data_operations_scheduler_activation_runbook.sh`

**Steps:**

1. Add syntax self-check.
2. Assert required docs/task files exist.
3. Assert runbook contains preflight, dry-run, manual approval, launchd reference, rollback, disable, and evidence markers.
4. Assert no script executes host scheduler mutation commands.
5. Run AWH for `data-operations-scheduler-activation-runbook`.

### Task 3: Roadmap And Handoff

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: prior data-operations verification scripts

**Steps:**

1. Mark `data-operations-scheduler-activation-runbook` as implemented.
2. Move immediate next task to `data-operations-scheduler-operator-dry-run`.
3. Update prior verification scripts so completed tasks remain aligned with the new next task.
4. Update handoff/review after verification.

### Task 4: Verification

**Commands:**

```bash
bash scripts/verify_data_operations_scheduler_activation_runbook.sh
bash scripts/verify_data_operations_scheduler_alert_boundary.sh
bash scripts/verify_project_execution_roadmap.sh
/tmp/stockanalysis-fastapi-venv/bin/python -m unittest discover -s tests
git diff --check
```
