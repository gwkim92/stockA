# Data Operations Scheduler Activation Approval Gate Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a machine-readable gate that blocks Data Operations scheduler activation unless operator dry-run evidence and explicit approval are present.

**Architecture:** A Python report builder validates the operator dry-run report and optional approval record. A Bash wrapper loads repo-outside JSON evidence and emits a secret-free gate report without executing host scheduler commands.

**Tech Stack:** Python stdlib, Bash, existing Agent Work Harness task docs.

---

### Task 1: Approval Gate Builder

**Files:**
- Create: `src/stockanalysis/operations/scheduler_activation_approval.py`
- Create: `tests/test_data_operations_scheduler_activation_approval.py`

**Steps:**

1. Add `build_data_operations_scheduler_activation_approval_gate_report`.
2. Validate operator dry-run report is passed and still not installed.
3. Return blocked when approval record is absent.
4. Validate approval record fields when present.
5. Reject missing risk acknowledgements and job mismatches.
6. Unit test blocked and approved paths.

### Task 2: Approval Gate Wrapper

**Files:**
- Create: `scripts/check_data_operations_scheduler_activation_approval_gate.sh`

**Steps:**

1. Parse `--operator-dry-run-report`, optional `--approval-record`, and optional `--output`.
2. Refuse repo-inside evidence/approval/output paths.
3. Load JSON and call the Python builder.
4. Print or write the report.
5. Do not call `launchctl`.

### Task 3: Verification Script

**Files:**
- Create: `scripts/verify_data_operations_scheduler_activation_approval_gate.sh`

**Steps:**

1. Run targeted unit tests.
2. Generate an operator dry-run evidence bundle using temp repo-outside paths.
3. Run the gate without approval and assert blocked.
4. Run the gate with a fixture approval record and assert approved but not activated.
5. Assert fake secrets do not leak.
6. Assert docs/roadmap/AGENTS/AWH markers.

### Task 4: Docs And Roadmap

**Files:**
- Create: `docs/data-operations-scheduler-activation-approval-gate.md`
- Modify: `docs/data-operations-scheduler-operator-dry-run.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: prior data-operations verification scripts

**Steps:**

1. Document the approval record shape.
2. Mark `data-operations-scheduler-activation-approval-gate` complete in roadmap.
3. Move immediate next task to `data-operations-live-scheduler-activation-request`.
4. Update handoff/review after verification.

### Task 5: Verification

**Commands:**

```bash
bash scripts/verify_data_operations_scheduler_activation_approval_gate.sh
bash scripts/verify_data_operations_scheduler_operator_dry_run.sh
bash scripts/verify_project_execution_roadmap.sh
PYTHONPATH=src /tmp/stockanalysis-full-venv/bin/python -m unittest discover -s tests
git diff --check
```
