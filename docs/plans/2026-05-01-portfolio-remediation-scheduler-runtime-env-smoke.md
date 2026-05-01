# Portfolio Remediation Scheduler Runtime Env Smoke Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** env file 기반으로 intended runtime DB에서 scheduler wrapper를 1회 smoke 실행할 수 있는 repo-local runner를 만든다.

**Architecture:** 기존 scheduler wrapper는 environment variable만 받으므로, 새 smoke runner는 trusted env file을 source한 뒤 wrapper run mode를 실행하고 JSON artifact, stderr artifact, latest DB pipeline status를 검증한다. 실제 production credentials는 저장하지 않고, Docker fixture 검증으로 runner 자체의 동작만 증명한다.

**Tech Stack:** Bash, Docker Postgres, Python stdlib JSON validation, existing `scripts/run_portfolio_remediation_daily_scheduler.sh`.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/contract.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/plan.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/handoff.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/review.md`

**Steps:**
- Scope를 env file 기반 runtime smoke runner로 제한한다.
- 실제 production DB credentials, host launchd install, `launchctl bootstrap`은 제외한다.
- 검증 명령을 고정한다.

### Task 2: Runtime Env Smoke Runner

**Files:**
- Create: `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh`

**Steps:**
- `--env-file PATH`를 필수 인자로 받는다.
- env file 존재와 scheduler wrapper executable을 확인한다.
- trusted env file을 `set -a; . "$ENV_FILE"; set +a` 방식으로 source한다.
- `scripts/run_portfolio_remediation_daily_scheduler.sh` run mode를 실행한다.
- wrapper가 출력한 JSON artifact path와 sibling stderr artifact를 검증한다.
- JSON payload의 `report_name`, `run_id`, BABA open ticket을 검증한다.
- `STOCKANALYSIS_PSQL_COMMAND`로 latest `portfolio_remediation_daily_automation` status가 `succeeded`인지 확인한다.

### Task 3: Docker Verification

**Files:**
- Create: `scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`

**Steps:**
- Docker Postgres를 시작한다.
- migrations/seeds와 prerequisite pipeline을 실행한다.
- temp env file을 만들어 `STOCKANALYSIS_PSQL_COMMAND`, dates, universe, artifact root를 설정한다.
- 새 smoke runner를 `--env-file`로 실행한다.
- runner output JSON summary와 created artifact를 검증한다.

### Task 4: Docs

**Files:**
- Create: `docs/portfolio-remediation-scheduler-runtime-env-smoke.md`
- Modify: `README.md`
- Modify: `docs/portfolio-remediation-scheduler-runtime-smoke.md`
- Modify: `docs/portfolio-remediation-scheduler-install.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-runtime-env-smoke/review.md`

**Steps:**
- env file smoke runner 목적과 boundary를 문서화한다.
- 실제 production DB와 launchd activation이 아직 남았다는 점을 명확히 적는다.
- verification evidence를 handoff/review에 남긴다.
