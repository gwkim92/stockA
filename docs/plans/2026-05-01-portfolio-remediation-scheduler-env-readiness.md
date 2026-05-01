# Portfolio Remediation Scheduler Env Readiness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** actual runtime DB smoke 전에 repo 밖 scheduler env file을 안전하게 만들고 preflight 검증할 수 있는 readiness gate를 만든다.

**Architecture:** production credentials는 repo에 저장하지 않는다. template renderer는 repo 밖 경로에 shell sourceable env template을 생성하고, readiness checker는 trusted env file을 source해 필수 변수, placeholder 잔존 여부, artifact root, wrapper preflight를 검증한다.

**Tech Stack:** Bash, Python stdlib path/date/json validation, existing scheduler wrapper preflight.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-scheduler-env-readiness/contract.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-env-readiness/plan.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-env-readiness/handoff.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-env-readiness/review.md`

**Steps:**
- Scope를 env file template/readiness preflight로 제한한다.
- actual DB smoke, host launchd install, `launchctl bootstrap`은 제외한다.
- 검증 명령을 고정한다.

### Task 2: Env Template Renderer

**Files:**
- Create: `scripts/render_portfolio_remediation_scheduler_env_template.sh`

**Steps:**
- `--output PATH`를 필수 인자로 받는다.
- output path가 repo 내부면 실패한다.
- 기존 파일이 있으면 `--force` 없이는 실패한다.
- shell source 가능한 env template을 렌더링한다.
- template에는 placeholder가 포함되어 readiness check에서 그대로는 실패해야 한다.

### Task 3: Env Readiness Checker

**Files:**
- Create: `scripts/check_portfolio_remediation_scheduler_runtime_env.sh`

**Steps:**
- `--env-file PATH`를 필수 인자로 받는다.
- env file이 repo 내부면 실패한다.
- trusted env file을 source한다.
- required env, ISO date format, positive ticket limit, absolute/writable artifact root를 검증한다.
- `STOCKANALYSIS_PSQL_COMMAND`가 shell split 가능하고 first command가 존재하는지 확인한다.
- placeholder 값이 남아 있으면 실패한다.
- `scripts/run_portfolio_remediation_daily_scheduler.sh --preflight-only`를 실행하고 JSON preflight payload를 검증한다.

### Task 4: Verification

**Files:**
- Create: `scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`

**Steps:**
- renderer/checker/wrapper syntax를 검증한다.
- repo 내부 output path 거부를 검증한다.
- template을 temp repo-outside path에 렌더링한다.
- unedited template readiness가 placeholder 때문에 실패하는지 확인한다.
- valid temp env file readiness가 통과하는지 확인한다.
- install dry-run이 valid temp env file과 호환되는지 확인한다.

### Task 5: Docs

**Files:**
- Create: `docs/portfolio-remediation-scheduler-env-readiness.md`
- Modify: `README.md`
- Modify: `docs/portfolio-remediation-scheduler-runtime-env-smoke.md`
- Modify: `docs/portfolio-remediation-scheduler-install.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-env-readiness/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-env-readiness/review.md`

**Steps:**
- env readiness 목적과 boundary를 문서화한다.
- actual DB smoke와 install이 아직 별도 gate라는 점을 명확히 적는다.
- verification evidence를 handoff/review에 남긴다.
