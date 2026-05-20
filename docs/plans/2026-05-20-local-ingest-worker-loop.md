# Local Ingest Worker Loop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the already-proven market/news/AI local ingest smoke runnable as a safe local process loop without Mac LaunchAgents, external scheduler deployment, or shell-owned product orchestration.

**Architecture:** Add a Python operations worker that delegates each cycle to the existing `manual-local-ingest-smoke` service boundary. The worker defaults to one preview cycle, requires `--execute` for DB/provider writes, supports bounded `--max-cycles`, and can update the existing repo-outside manual smoke summary file so `/data-health` continues to show the latest local run evidence.

**Tech Stack:** Python `stockanalysis.operations` CLI/service boundary, existing artifact runner, repo-outside JSON reports, unittest.

---

### Task 1: Record Guardrail

**Files:**
- Create: `docs/tasks/local-ingest-worker-loop/contract.md`
- Modify: `AGENTS.md`
- Modify: `docs/project-execution-roadmap.md`

**Steps:**
- Record that this is a local process worker, not a Mac LaunchAgent install and not an external scheduler decision.
- Keep DB schema, scoring, paid LLM, broker/order flow, and host scheduler mutation out of scope.

### Task 2: Add Worker Service

**Files:**
- Create: `src/stockanalysis/operations/local_ingest_worker.py`
- Test: `tests/test_local_ingest_worker.py`

**Steps:**
- Implement `run_local_ingest_worker` with bounded `max_cycles`, `interval_seconds`, `execute`, `stop_on_failure`, `job_ids`, and optional repo-outside `smoke_output_path`.
- Delegate cycle execution to `build_manual_local_ingest_smoke_report`.
- Write the latest cycle smoke summary to `smoke_output_path` when configured.
- Return a secret-free worker report with cycle summaries and host mutation flags set to false.

### Task 3: Add CLI Boundary

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_data_operations_cli.py`

**Steps:**
- Add `stockanalysis-operations local-ingest-worker-run`.
- Support `--runtime-root`, `--data-operations-env-file`, `--artifact-root`, `--job-id`, `--execute`, `--max-cycles`, `--interval-seconds`, `--timeout-seconds`, `--python-executable`, `--smoke-output`, `--output`, and `--continue-on-failure`.
- Reject repo-inside output paths through existing path policy.

### Task 4: Verify and Handoff

**Files:**
- Create: `scripts/verify_local_ingest_worker_loop.sh`
- Create: `docs/local-ingest-worker-loop.md`
- Create: `docs/tasks/local-ingest-worker-loop/handoff.md`
- Create: `docs/tasks/local-ingest-worker-loop/review.md`
- Modify: `docs/verification-plan.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Steps:**
- Run focused unit tests.
- Run a no-write preview CLI smoke against a repo-outside temp runtime root.
- Run roadmap verification, AWH task verification, and diff whitespace check.
