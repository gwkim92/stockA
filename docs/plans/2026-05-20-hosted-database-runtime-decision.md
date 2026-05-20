# Hosted Database Runtime Decision Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Decide the zero-budget hosted database/runtime path that unblocks future GitHub Actions scheduled ingest without provisioning anything.

**Architecture:** Add a decision builder that evaluates local-only, Supabase Free Postgres, existing host Postgres, Render Free Postgres, and GitHub Actions worker compatibility. The default output recommends Supabase Free Postgres + GitHub Actions worker as the next setup path, but keeps deployment blocked until the user creates the hosted DB and supplies repo-outside secrets.

**Tech Stack:** Python stdlib, `stockanalysis-operations` CLI, shell verification, AWH task docs.

---

### Task 1: Contract And Decision Notes

**Files:**
- Create: `docs/tasks/hosted-database-runtime-decision/contract.md`
- Create: `docs/hosted-database-runtime-decision.md`

**Steps:**
1. Document the zero-budget constraint.
2. Document why external scheduler cannot use local Postgres.
3. Document Supabase Free as the first recommended hosted DB candidate and Render Free Postgres as blocked due 30-day expiry.

### Task 2: Decision Builder

**Files:**
- Create: `src/stockanalysis/operations/hosted_runtime_decision.py`
- Test: `tests/test_hosted_runtime_decision.py`

**Steps:**
1. Add tests for default state: setup required, recommended path Supabase Free + GitHub Actions.
2. Add tests for configured hosted DB: ready for hosted DB migration smoke.
3. Add tests for existing host: prefer existing host if already available.
4. Add tests for local-only accepted: marks scheduler as local-only, not external.

### Task 3: CLI

**Files:**
- Modify: `src/stockanalysis/operations/cli.py`
- Modify: `tests/test_data_operations_cli.py`

**Steps:**
1. Add `hosted-database-runtime-decision` command.
2. Add output and markdown output support.
3. Reject repo-inside output.
4. Ensure report is secret-free.

### Task 4: Verification

**Files:**
- Create: `scripts/verify_hosted_database_runtime_decision.sh`

**Steps:**
1. Run compileall and focused unit/CLI tests.
2. Run CLI smoke for default decision.
3. Assert no DB URL/API key/token and no provisioning artifact.

### Task 5: Roadmap

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/verification-plan.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Create: `docs/tasks/hosted-database-runtime-decision/handoff.md`
- Create: `docs/tasks/hosted-database-runtime-decision/review.md`

**Steps:**
1. Mark this decision as implemented.
2. Move immediate next task to `supabase-free-postgres-setup-packet`.
3. Record verification evidence.
