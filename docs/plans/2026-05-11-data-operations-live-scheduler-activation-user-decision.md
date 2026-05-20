# Data Operations Live Scheduler Activation User Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a safe user-decision gate for live Data Operations scheduler activation.

**Architecture:** The Python report builder validates a pending activation request and an optional repo-outside decision record. The shell wrapper enforces repo-outside input/output paths and never invokes host scheduler mutation commands.

**Tech Stack:** Python stdlib, Bash, unittest, Agent Work Harness task docs.

---

### Task 1: Report Builder

**Files:**
- Create: `src/stockanalysis/operations/scheduler_activation_decision.py`
- Test: `tests/test_data_operations_scheduler_activation_decision.py`

**Step 1: Write the failing test**

Add tests for missing decision, approve decision, deny decision, mismatched request path, and secret-like operator note rejection.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_decision -v`
Expected: FAIL because the module does not exist.

**Step 3: Write minimal implementation**

Add `build_data_operations_live_scheduler_activation_user_decision_report()` that validates pending request reports and explicit decision records.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_decision -v`
Expected: PASS.

### Task 2: Wrapper Script

**Files:**
- Create: `scripts/decide_data_operations_live_scheduler_activation.sh`
- Create: `scripts/verify_data_operations_live_scheduler_activation_user_decision.sh`

**Step 1: Add script syntax and path guard checks**

Use `bash -n` and repo-inside refusal checks in the verification script.

**Step 2: Implement wrapper**

Read repo-outside activation request and optional decision records, then write the decision report only outside the repository.

**Step 3: Verify no activation side effect**

Run: `grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/decide_data_operations_live_scheduler_activation.sh`
Expected: no match.

### Task 3: End-to-End Verification

**Files:**
- Create: `scripts/verify_data_operations_live_scheduler_activation_user_decision.sh`

**Step 1: Generate request evidence**

Use existing operator dry-run, approval gate, and activation request scripts in a temp directory.

**Step 2: Generate user decision reports**

Run the new decision wrapper without a decision, with approve, and with deny records.

**Step 3: Check blocked paths**

Assert secret-like decision records and repo-inside evidence paths are rejected.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/data-operations-live-scheduler-activation-user-decision.md`
- Create: `docs/tasks/data-operations-live-scheduler-activation-user-decision/*`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Step 1: Document the boundary**

State that this task never runs `launchctl` and only records a decision gate result.

**Step 2: Move the fixed next task**

Set immediate next to `data-operations-live-scheduler-activation-final-preflight`.

**Step 3: Run verification**

Run targeted verification, roadmap verification, AWH verification, full unittest, and `git diff --check`.
