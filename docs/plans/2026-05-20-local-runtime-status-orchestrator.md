# Local Runtime Status Orchestrator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 로컬에서 Postgres/env/API/화면/operations worker 준비 상태를 한 번에 확인하는 read-only status command를 만든다.

**Architecture:** Product orchestration logic stays in `stockanalysis-operations`, not shell scripts. The command reads repo-outside env files, redacts all values, probes local FastAPI/Next endpoints when requested, and prints an actionable JSON report without starting services or installing schedulers.

**Tech Stack:** Python stdlib `argparse`, `urllib.request`, existing operations CLI, unittest, thin Bash verification wrapper.

---

### Task 1: Status Report Core

**Files:**
- Create: `src/stockanalysis/operations/local_runtime_status.py`
- Test: `tests/test_local_runtime_status_orchestrator.py`

**Step 1: Write tests for secret-free status output**

Verify env values such as database passwords and provider keys are not included in JSON output.

**Step 2: Implement local runtime report builder**

Return component status for runtime root, frontend env, data operations env, database boundary, artifact root, FastAPI live endpoint, and Next cockpit endpoint.

**Step 3: Add launchctl guardrail explanation**

Include `codex_host_mutation_allowed=false` and reasons why LaunchAgents remain blocked.

### Task 2: CLI Boundary

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_data_operations_cli.py`

**Step 1: Add `local-runtime-status` parser**

Expose `--runtime-root`, `--frontend-api-env-file`, `--data-operations-env-file`, `--frontend-api-url`, `--next-url`, `--http-timeout-seconds`, and `--skip-http-probes`.

**Step 2: Add CLI test**

Verify the command prints `local_first_runtime_status`, returns `0`, and does not expose env values.

### Task 3: Verification Script

**Files:**
- Create: `scripts/verify_local_runtime_status_orchestrator.sh`

**Step 1: Add thin verification wrapper**

Run shell syntax check, compileall, targeted unittest, and a no-probe CLI smoke.

**Step 2: Keep script thin**

Do not put product orchestration logic in shell.

### Task 4: Docs And Handoff

**Files:**
- Create: `docs/local-runtime-status-orchestrator.md`
- Create: `docs/tasks/local-runtime-status-orchestrator/contract.md`
- Create: `docs/tasks/local-runtime-status-orchestrator/handoff.md`
- Create: `docs/tasks/local-runtime-status-orchestrator/review.md`
- Modify: `docs/local-first-runtime-direction.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`

**Step 1: Document why LaunchAgents remain blocked**

Explain persistent host mutation, unattended secret-bearing execution, audit/rollback concerns, and why manual local worker status is enough now.

**Step 2: Update immediate next task**

Move immediate next to `local-runtime-status-orchestrator` after the direction decision.

### Task 5: Verification

**Files:**
- Update: `docs/tasks/local-runtime-status-orchestrator/handoff.md`
- Update: `docs/tasks/local-runtime-status-orchestrator/review.md`

**Step 1: Run targeted verification**

Run `bash scripts/verify_local_runtime_status_orchestrator.sh`.

**Step 2: Run roadmap and harness checks**

Run `bash scripts/verify_project_execution_roadmap.sh` and AWH for `local-runtime-status-orchestrator`.

**Step 3: Run whitespace check**

Run `git diff --check`.
