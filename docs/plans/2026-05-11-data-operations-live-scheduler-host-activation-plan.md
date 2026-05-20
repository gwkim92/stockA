# Data Operations Live Scheduler Host Activation Plan Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a host activation plan artifact from final preflight evidence without executing scheduler commands.

**Architecture:** The Python report builder validates a passing final preflight and activation request report, then emits JSON plan metadata and a Markdown operator review document. The shell wrapper enforces repo-outside evidence/output paths and writes artifacts only to the caller-provided output directory.

**Tech Stack:** Python stdlib, Bash, unittest, Agent Work Harness task docs.

---

### Task 1: Report Builder

**Files:**
- Create: `src/stockanalysis/operations/scheduler_activation_host_plan.py`
- Test: `tests/test_data_operations_scheduler_activation_host_plan.py`

**Step 1: Write the failing test**

Add tests for plan creation, Markdown rendering, blocked final preflight rejection, path mismatch rejection, and secret-like command preview rejection.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_host_plan -v`
Expected: FAIL because the module does not exist.

**Step 3: Write minimal implementation**

Add `build_data_operations_live_scheduler_host_activation_plan_report()` and Markdown rendering with all mutation flags false.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_host_plan -v`
Expected: PASS.

### Task 2: Wrapper Script

**Files:**
- Create: `scripts/plan_data_operations_live_scheduler_host_activation.sh`
- Create: `scripts/verify_data_operations_live_scheduler_host_activation_plan.sh`

**Step 1: Add script syntax and path guard checks**

Use `bash -n` and repo-inside refusal checks in the verification script.

**Step 2: Implement wrapper**

Read repo-outside final preflight evidence, derive activation request evidence, and write JSON/Markdown plan artifacts outside the repository.

**Step 3: Verify no activation side effect**

Run: `grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/plan_data_operations_live_scheduler_host_activation.sh`
Expected: no match.

### Task 3: End-to-End Verification

**Files:**
- Create: `scripts/verify_data_operations_live_scheduler_host_activation_plan.sh`

**Step 1: Generate activation evidence chain**

Use existing operator dry-run, approval gate, activation request, user decision, and final preflight scripts in a temp directory.

**Step 2: Run host activation plan**

Run the plan wrapper and assert JSON/Markdown outputs contain command previews but no secret values.

**Step 3: Check blocked paths**

Assert denied preflight and repo-inside evidence/output paths are rejected.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/data-operations-live-scheduler-host-activation-plan.md`
- Create: `docs/tasks/data-operations-live-scheduler-host-activation-plan/*`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Step 1: Document the boundary**

State that this task never runs `launchctl` and only permits a future execution request.

**Step 2: Move the fixed next task**

Set immediate next to `data-operations-live-scheduler-host-activation-execution-request`.

**Step 3: Run verification**

Run targeted verification, roadmap verification, AWH verification, full unittest, and `git diff --check`.
