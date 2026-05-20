# Server Scheduler Deployment Target Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Decide the next scheduler deployment target under the zero-budget and current local-runtime constraints without deploying anything.

**Architecture:** Add a small operations decision builder that scores scheduler candidates from explicit constraints and emits a secret-free decision packet. The packet can recommend GitHub Actions as the future no-server scheduler candidate while blocking deployment when the database/runtime is still local-only.

**Tech Stack:** Python stdlib, `stockanalysis-operations` CLI, AWH task docs, shell verification.

---

### Task 1: Task Contract

**Files:**
- Create: `docs/tasks/server-scheduler-deployment-target-decision/contract.md`
- Create: `docs/server-scheduler-deployment-target-decision.md`

**Steps:**
1. Document that this task does not deploy cron/systemd/Kubernetes/GitHub Actions.
2. Document that zero budget is a hard constraint.
3. Document that local-only Postgres blocks external scheduler deployment.

### Task 2: Decision Builder

**Files:**
- Create: `src/stockanalysis/operations/server_scheduler_deployment_decision.py`
- Test: `tests/test_server_scheduler_deployment_decision.py`

**Steps:**
1. Add tests for current constraints: public repo, zero budget, no hosted DB, no runtime host, Mac scheduler not allowed.
2. Implement a report with candidate matrix and blocked decision.
3. Add tests for hosted DB configured: GitHub Actions becomes recommended.
4. Add tests for existing runtime host: systemd timer becomes recommended.

### Task 3: CLI

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Modify: `tests/test_data_operations_cli.py`

**Steps:**
1. Add `server-scheduler-deployment-target-decision` command.
2. Add output and markdown output support.
3. Reject repo-inside output paths.
4. Verify no secret-like values are emitted.

### Task 4: Verification

**Files:**
- Create: `scripts/verify_server_scheduler_deployment_target_decision.sh`

**Steps:**
1. Run compileall and focused unit/CLI tests.
2. Run a CLI smoke for the current blocked decision.
3. Assert no `launchctl`, DB URL, API key, or scheduler deployment artifact.

### Task 5: Roadmap And Handoff

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Create: `docs/tasks/server-scheduler-deployment-target-decision/handoff.md`
- Create: `docs/tasks/server-scheduler-deployment-target-decision/review.md`

**Steps:**
1. Mark this task as implemented.
2. Move immediate next task to `hosted-database-runtime-decision`.
3. Record verification evidence and residual risks.
