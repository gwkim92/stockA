# Data Operations Live Scheduler Host Activation Execution Request Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an explicit host activation execution request packet from a reviewed host activation plan without executing scheduler commands.

**Architecture:** A Python report builder validates the host activation plan artifact and emits a secret-free request packet that asks for explicit execution approval. A Bash wrapper enforces repo-outside input/output paths and writes only JSON metadata. The next task becomes an execution decision gate; actual host mutation remains out of scope.

**Tech Stack:** Python stdlib, Bash, unittest, Agent Work Harness task docs.

---

### Task 1: Task Contract And Scope

**Files:**
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-request/contract.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-request/plan.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-request/handoff.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-execution-request/review.md`

**Step 1: Write the task contract**

Capture that this task only requests explicit execution approval and must not run `launchctl`, write LaunchAgents, or run the child job.

**Step 2: Write implementation handoff scaffolding**

Add plan, handoff, and review files before code changes.

### Task 2: Report Builder

**Files:**
- Create: `src/stockanalysis/operations/scheduler_activation_execution_request.py`
- Test: `tests/test_data_operations_scheduler_activation_execution_request.py`

**Step 1: Write the failing test**

Test ready host plan -> pending execution approval request, non-ready plan rejection, missing command previews, executed step rejection, and secret-like request note rejection.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_execution_request -v`
Expected: FAIL because the module does not exist.

**Step 3: Implement the builder**

Add `build_data_operations_live_scheduler_host_activation_execution_request_report()` with all mutation flags false, explicit requested decision values, copied command previews, and `manual_next_step = data-operations-live-scheduler-host-activation-execution-decision`.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_execution_request -v`
Expected: PASS.

### Task 3: Wrapper Script

**Files:**
- Create: `scripts/request_data_operations_live_scheduler_host_activation_execution.sh`

**Step 1: Add CLI path guards**

Refuse repo-inside host activation plan reports and repo-inside output paths.

**Step 2: Write JSON request output**

Load the host activation plan report, call the builder, and print or write JSON output.

**Step 3: Verify no host mutation command**

Run: `grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/request_data_operations_live_scheduler_host_activation_execution.sh`
Expected: no match.

### Task 4: End-To-End Verification

**Files:**
- Create: `scripts/verify_data_operations_live_scheduler_host_activation_execution_request.sh`

**Step 1: Build evidence chain**

Use operator dry-run, approval gate, activation request, user decision, final preflight, and host activation plan scripts in repo-outside temp paths.

**Step 2: Request execution approval**

Run the execution request wrapper and assert output is `pending_explicit_execution_approval`, contains command previews, has all execution flags false, and leaks no fake secret values.

**Step 3: Check blocked paths and malformed plan**

Assert repo-inside inputs/outputs, non-ready plan reports, and secret-like request notes fail.

### Task 5: Docs And Roadmap

**Files:**
- Create: `docs/data-operations-live-scheduler-host-activation-execution-request.md`
- Modify: `docs/data-operations-live-scheduler-host-activation-plan.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: prior data operations verify scripts that assert immediate next task

**Step 1: Document the safety boundary**

State that this task only requests explicit execution approval.

**Step 2: Move the fixed next task**

Set immediate next to `data-operations-live-scheduler-host-activation-execution-decision`.

**Step 3: Run verification**

Run targeted verification, roadmap verification, full unittest, and `git diff --check`.
