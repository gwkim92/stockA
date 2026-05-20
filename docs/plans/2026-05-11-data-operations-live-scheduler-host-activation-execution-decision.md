# Data Operations Live Scheduler Host Activation Execution Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Validate approve/deny host activation execution decision records without executing scheduler commands.

**Architecture:** A Python report builder validates the pending execution request and an optional repo-outside execution decision record. It emits missing/approved/denied decision gate reports while preserving all host mutation flags as false. A Bash wrapper enforces repo-outside evidence/output paths and writes only JSON metadata.

**Tech Stack:** Python stdlib, Bash, unittest, Agent Work Harness task docs.

---

### Task 1: Task Contract And Scope

**Files:**
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-decision/contract.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-decision/plan.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-decision/handoff.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-decision/review.md`

**Step 1: Write the task contract**

Capture that this task only validates approve/deny execution decisions and must not run `launchctl`, write LaunchAgents, or run the child job.

**Step 2: Write implementation handoff scaffolding**

Add plan, handoff, and review files before code changes.

### Task 2: Report Builder

**Files:**
- Create: `src/stockanalysis/operations/scheduler_activation_execution_decision.py`
- Test: `tests/test_data_operations_scheduler_activation_execution_decision.py`

**Step 1: Write the failing test**

Test missing decision, approve decision, deny decision, bad execution request rejection, path mismatch rejection, and secret-like operator note rejection.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_execution_decision -v`
Expected: FAIL because the module does not exist.

**Step 3: Implement the builder**

Add `build_data_operations_live_scheduler_host_activation_execution_decision_report()` with all mutation flags false and approve moving only to `data-operations-live-scheduler-host-activation-execution-final-preflight`.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_execution_decision -v`
Expected: PASS.

### Task 3: Wrapper Script

**Files:**
- Create: `scripts/decide_data_operations_live_scheduler_host_activation_execution.sh`

**Step 1: Add CLI path guards**

Refuse repo-inside execution request reports, decision records, and output paths.

**Step 2: Write JSON decision output**

Load the execution request report and optional decision record, call the builder, and print or write JSON output.

**Step 3: Verify no host mutation command**

Run: `grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/decide_data_operations_live_scheduler_host_activation_execution.sh`
Expected: no match.

### Task 4: End-To-End Verification

**Files:**
- Create: `scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh`

**Step 1: Build evidence chain**

Use operator dry-run, approval gate, activation request, user decision, final preflight, host activation plan, and execution request scripts in repo-outside temp paths.

**Step 2: Validate execution decisions**

Run the execution decision wrapper for missing, approve, and deny records. Assert approve only moves to final preflight and no host mutation flags change.

**Step 3: Check blocked paths and malformed records**

Assert repo-inside inputs/outputs, mismatched request paths, and secret-like operator notes fail.

### Task 5: Docs And Roadmap

**Files:**
- Create: `docs/data-operations-live-scheduler-host-activation-execution-decision.md`
- Modify: `docs/data-operations-live-scheduler-host-activation-execution-request.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: prior data operations verify scripts that assert immediate next task

**Step 1: Document the safety boundary**

State that this task only validates execution decisions.

**Step 2: Move the fixed next task**

Set immediate next to `data-operations-live-scheduler-host-activation-execution-final-preflight`.

**Step 3: Run verification**

Run targeted verification, roadmap verification, full unittest, and `git diff --check`.
