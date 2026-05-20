# Data Operations Live Scheduler Activation Final Preflight Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a final preflight gate that revalidates approved scheduler activation evidence and runtime env readiness without mutating host scheduler state.

**Architecture:** The Python report builder validates the decision/request/approval/dry-run evidence chain and a fresh runtime readiness report. The shell wrapper enforces repo-outside input/output paths, sources the env file only to produce a redacted readiness report, and writes final preflight evidence outside the repository.

**Tech Stack:** Python stdlib, Bash, unittest, Agent Work Harness task docs.

---

### Task 1: Report Builder

**Files:**
- Create: `src/stockanalysis/operations/scheduler_activation_final_preflight.py`
- Test: `tests/test_data_operations_scheduler_activation_final_preflight.py`

**Step 1: Write the failing test**

Add tests for approved decision passing, denied decision blocking, runtime readiness failure blocking, mismatched paths, and secret-like runtime payload rejection.

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_final_preflight -v`
Expected: FAIL because the module does not exist.

**Step 3: Write minimal implementation**

Add `build_data_operations_live_scheduler_activation_final_preflight_report()` that validates evidence and produces a final preflight report with all mutation flags false.

**Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_scheduler_activation_final_preflight -v`
Expected: PASS.

### Task 2: Wrapper Script

**Files:**
- Create: `scripts/preflight_data_operations_live_scheduler_activation.sh`
- Create: `scripts/verify_data_operations_live_scheduler_activation_final_preflight.sh`

**Step 1: Add script syntax and path guard checks**

Use `bash -n` and repo-inside refusal checks in the verification script.

**Step 2: Implement wrapper**

Read repo-outside activation decision evidence, derive request/approval/operator evidence paths, generate fresh runtime readiness, and write final preflight output outside the repository.

**Step 3: Verify no activation side effect**

Run: `grep -Eq '^[[:space:]]*launchctl[[:space:]]' scripts/preflight_data_operations_live_scheduler_activation.sh`
Expected: no match.

### Task 3: End-to-End Verification

**Files:**
- Create: `scripts/verify_data_operations_live_scheduler_activation_final_preflight.sh`

**Step 1: Generate activation evidence chain**

Use existing operator dry-run, approval gate, activation request, and user decision scripts in a temp directory.

**Step 2: Run final preflight**

Run final preflight for approved and denied decision reports.

**Step 3: Check blocked paths**

Assert repo-inside decision/env/output paths are rejected and secret fixture values do not leak.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/data-operations-live-scheduler-activation-final-preflight.md`
- Create: `docs/tasks/data-operations-live-scheduler-activation-final-preflight/*`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `AGENTS.md`

**Step 1: Document the boundary**

State that this task never runs `launchctl` and only permits a future host activation plan.

**Step 2: Move the fixed next task**

Set immediate next to `data-operations-live-scheduler-host-activation-plan`.

**Step 3: Run verification**

Run targeted verification, roadmap verification, AWH verification, full unittest, and `git diff --check`.
