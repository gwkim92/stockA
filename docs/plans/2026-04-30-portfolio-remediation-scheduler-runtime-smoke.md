# Portfolio Remediation Scheduler Runtime Smoke Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Docker Postgres runtime에서 `scripts/run_portfolio_remediation_daily_scheduler.sh` run mode가 daily remediation JSON/stderr artifact를 만들고 DB pipeline status를 성공으로 남기는지 검증한다.

**Architecture:** 기존 daily automation integration path와 같은 prerequisite data를 Docker Postgres에 만든다. 마지막 실행만 직접 CLI가 아니라 scheduler wrapper를 통해 수행해 artifact capture, JSON validation, DB run status를 함께 확인한다. 실제 host launchd install은 실행하지 않는다.

**Tech Stack:** Bash integration script, Docker Postgres, Python stdlib JSON validation, existing scheduler wrapper.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/contract.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/plan.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/handoff.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/review.md`

**Steps:**
- Scope를 Docker runtime smoke로 제한한다.
- 실제 host scheduler install, live production DB, external alert는 제외한다.
- 검증 명령을 고정한다.

### Task 2: Runtime Smoke Script

**Files:**
- Create: `scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`

**Steps:**
- Docker Postgres를 시작한다.
- migrations/seeds와 prerequisite pipeline을 실행한다.
- `scripts/run_portfolio_remediation_daily_scheduler.sh` run mode를 Docker `STOCKANALYSIS_PSQL_COMMAND`와 temp artifact root로 실행한다.
- wrapper가 출력한 JSON artifact path가 존재하는지 확인한다.
- stderr log artifact가 존재하는지 확인한다.
- JSON payload와 DB latest pipeline status를 검증한다.

### Task 3: Docs

**Files:**
- Create: `docs/portfolio-remediation-scheduler-runtime-smoke.md`
- Modify: `README.md`
- Modify: `docs/portfolio-remediation-scheduler-install.md`
- Modify: `docs/portfolio-remediation-scheduler-activation.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-runtime-smoke/review.md`

**Steps:**
- runtime smoke 목적과 boundary를 문서화한다.
- verification evidence를 handoff/review에 남긴다.
