# Data Operations Live Scheduler Activation Request Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a safe activation request packet that turns approved scheduler activation evidence into a pending explicit user decision.

**Architecture:** The Python report builder validates an approved activation gate plus operator dry-run evidence, then returns a secret-free JSON report with command previews and no side effects. The shell wrapper enforces repo-outside evidence/output paths and delegates only JSON validation/rendering to Python.

**Tech Stack:** Python stdlib, Bash, unittest, Agent Work Harness task docs.

---

### Task 1: Report Builder

**Files:**
- Create: `src/stockanalysis/operations/scheduler_activation_request.py`
- Test: `tests/test_data_operations_scheduler_activation_request.py`

**Step 1: Write the failing test**

Add tests for approved gate request generation, pending gate rejection, path mismatch rejection, and secret-like request note rejection.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_request -v`
Expected: FAIL because the module does not exist.

**Step 3: Write minimal implementation**

Add `build_data_operations_live_scheduler_activation_request_report()` that validates gate/operator reports, emits `pending_explicit_user_approval`, and marks all mutation flags false.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_request -v`
Expected: PASS.

### Task 2: Wrapper Script

**Files:**
- Create: `scripts/request_data_operations_live_scheduler_activation.sh`
- Modify: `scripts/verify_data_operations_live_scheduler_activation_request.sh`

**Step 1: Add script syntax and path guard tests**

Use `bash -n` and repo-inside refusal checks in the verification script.

**Step 2: Implement wrapper**

Read repo-outside approval gate and operator dry-run reports, derive operator report path from the gate when omitted, and write the request report only outside the repository.

**Step 3: Verify no activation side effect**

Run: `grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/request_data_operations_live_scheduler_activation.sh`
Expected: no match.

### Task 3: End-to-End Verification

**Files:**
- Create: `scripts/verify_data_operations_live_scheduler_activation_request.sh`

**Step 1: Generate fixture evidence**

Use the existing operator dry-run and approval gate scripts in a temp directory.

**Step 2: Generate activation request**

Run the new request wrapper with approved evidence and assert the output remains pending.

**Step 3: Check blocked paths**

Assert pending gate reports and repo-inside evidence paths are rejected.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/data-operations-live-scheduler-activation-request.md`
- Create: `docs/tasks/data-operations-live-scheduler-activation-request/*`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Step 1: Document the boundary**

State that this task never runs `launchctl` and only asks for explicit user approval.

**Step 2: Move the fixed next task**

Set immediate next to `data-operations-live-scheduler-activation-user-decision`.

**Step 3: Run verification**

Run targeted verification, roadmap verification, AWH verification, full unittest, and `git diff --check`.
