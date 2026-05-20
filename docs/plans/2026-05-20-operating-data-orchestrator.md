# Operating Data Orchestrator Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace EC2/manual ad hoc operating-data repair commands with a repeatable `stockanalysis-operations` backend runner that keeps market data, signal/recommendation, portfolio review, performance readiness, and paper validation aligned.

**Architecture:** Add a Python operations orchestrator that builds a secret-free run plan, validates repo-outside runtime paths, derives dates and symbol gaps from the database, generates transient repo-outside CSV inputs, and delegates every write step through the existing artifact runner. The runner defaults to preview mode, requires `--execute` for writes, never unlocks broker submission, and records the latest operating-data run as repo-outside JSON evidence for `/data-health` visibility.

**Tech Stack:** Python `stockanalysis.operations` CLI/service boundary, existing artifact runner, existing `stockanalysis-ingest` commands, repo-outside CSV/JSON artifacts, unittest, Postgres read queries through the existing scalar executor interface.

---

### Task 1: Record Contract

**Files:**
- Create: `docs/tasks/operating-data-orchestrator/contract.md`
- Create: `docs/tasks/operating-data-orchestrator/handoff.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`

**Steps:**
- Record the root cause: operating-data freshness and derived rows were manually sequenced, so missing symbols/dates could break read-only pages.
- Keep scheduler deployment, paid providers, DB schema changes, scoring formula changes, and real broker submission out of scope.
- Define the first done state as preview/execute CLI evidence plus focused tests.

### Task 2: Add Orchestrator Service

**Files:**
- Create: `src/stockanalysis/operations/operating_data_orchestrator.py`
- Test: `tests/test_operating_data_orchestrator.py`

**Steps:**
- Implement `build_operating_data_run_report` with `execute=False` preview by default.
- Resolve `data_operations_env_file`, `artifact_root`, `runtime_root`, and generated CSV/report paths with repo-outside policy.
- Use DB metadata queries to derive latest price date, latest event date, event-impacted symbols missing fresh prices, and portfolio source positions.
- Generate missing-symbol watchlist and normalized position snapshot CSV under the runtime root only when `--execute` is set.
- Delegate commands through `run_data_operation_artifact_command` in this order: missing-symbol market backfill, signal/recommendation chain, portfolio position snapshot, portfolio remediation, performance outcome schedule, paper safety config, paper validation audit.
- Return a secret-free report with planned steps, artifact summaries, derived inputs, and next actions.

### Task 3: Add CLI Boundary

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Test: `tests/test_data_operations_cli.py`

**Steps:**
- Add `stockanalysis-operations operating-data-run`.
- Support `--runtime-root`, `--data-operations-env-file`, `--artifact-root`, `--execute`, `--output`, `--python-executable`, `--portfolio-name`, `--strategy-name`, `--horizon-type`, `--market-code`, `--universe-version`, and budget/paper options.
- Reject repo-inside output/env/generated paths with the existing path policy.

### Task 4: Fix Data-Health Semantics

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Treat `portfolio-attribution-monthly` as `not_due` when no thesis outcome rows exist yet.
- Keep true missing/stale/failed jobs as `attention_required`.
- Add SQL marker tests so this is not a UI-only label change.

### Task 5: Verify and Handoff

**Files:**
- Create: `scripts/verify_operating_data_orchestrator.sh`
- Modify: `docs/tasks/operating-data-orchestrator/handoff.md`

**Steps:**
- Run focused unit tests for orchestrator, CLI, and data-health SQL.
- Run compileall and diff whitespace checks.
- Execute preview CLI smoke with repo-outside temp paths.
- If local checks pass, deploy to EC2 and run `operating-data-run --execute` once against the existing runtime env.
