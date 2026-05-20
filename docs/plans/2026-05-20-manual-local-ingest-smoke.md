# Manual Local Ingest Smoke Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** local-first runtime에서 market/news/AI 수동 수집 smoke를 preview-first 방식으로 실행하고 artifact를 남기는 operations CLI를 만든다.

**Architecture:** `stockanalysis-operations manual-local-ingest-smoke` builds a secret-free plan from repo-outside env files and local runtime status. By default it prints the planned operations without executing them; only `--execute` invokes the existing artifact runner for known cadence jobs.

**Tech Stack:** Python stdlib `argparse`, existing `stockanalysis.operations.artifact_runner`, existing local runtime status report, unittest, thin Bash verification wrapper.

---

### Task 1: Smoke Planner And Executor

**Files:**
- Create: `src/stockanalysis/operations/manual_local_ingest_smoke.py`
- Test: `tests/test_manual_local_ingest_smoke.py`

**Step 1: Write preview tests**

Verify preview mode returns planned market/news/AI jobs, does not call the runner, and emits no env values.

**Step 2: Write execution tests**

Verify `execute=True` calls the artifact runner in deterministic order and aggregates artifact metadata.

**Step 3: Implement the planner**

Resolve the repo-outside data operations env file, derive the artifact root, build safe command argv, and redact command values.

### Task 2: CLI Boundary

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_data_operations_cli.py`

**Step 1: Add `manual-local-ingest-smoke` parser**

Expose `--runtime-root`, `--data-operations-env-file`, `--artifact-root`, `--job-id`, `--execute`, `--timeout-seconds`, and `--python-executable`.

**Step 2: Add CLI smoke tests**

Verify preview exits `0`, execution failure exits `1`, and secrets are not printed.

### Task 3: Verification Script

**Files:**
- Create: `scripts/verify_manual_local_ingest_smoke.sh`

**Step 1: Add targeted verification**

Run shell syntax check, compileall, targeted unittest, and a no-execute CLI smoke.

**Step 2: Keep shell thin**

No product orchestration logic goes into shell.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/manual-local-ingest-smoke.md`
- Create: `docs/tasks/manual-local-ingest-smoke/contract.md`
- Create: `docs/tasks/manual-local-ingest-smoke/handoff.md`
- Create: `docs/tasks/manual-local-ingest-smoke/review.md`
- Modify: `docs/local-runtime-status-orchestrator.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Step 1: Document preview-first execution**

Explain that `--execute` is required before provider/DB writes happen.

**Step 2: Document next handoff**

Next work is `/data-health` visibility for latest manual smoke artifact.

### Task 5: Verification

**Files:**
- Update: `docs/tasks/manual-local-ingest-smoke/handoff.md`
- Update: `docs/tasks/manual-local-ingest-smoke/review.md`

**Step 1: Run targeted verification**

Run `bash scripts/verify_manual_local_ingest_smoke.sh`.

**Step 2: Run roadmap and harness checks**

Run `bash scripts/verify_project_execution_roadmap.sh` and AWH for `manual-local-ingest-smoke`.

**Step 3: Run whitespace check**

Run `git diff --check`.
