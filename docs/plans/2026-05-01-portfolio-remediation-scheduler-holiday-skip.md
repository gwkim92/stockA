# Portfolio Remediation Scheduler Holiday Skip Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** scheduler wrapper가 configured market holiday 또는 skip date에는 DB runner를 실행하지 않고 skip artifact만 남기게 한다.

**Architecture:** wrapper에 optional `PORTFOLIO_REMEDIATION_RUN_DATE`, `PORTFOLIO_REMEDIATION_SKIP_DATES`, `PORTFOLIO_REMEDIATION_SKIP_REASON`을 추가한다. run date가 skip list에 포함되면 stdout JSON path와 stderr artifact를 만들고, `portfolio-remediation-daily-run`은 호출하지 않는다. 실제 NYSE calendar sync는 별도 task로 남기고 현재는 explicit skip dates만 지원한다.

**Tech Stack:** Bash wrapper, Python stdlib JSON validation, existing scheduler activation verification.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-scheduler-holiday-skip/contract.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-holiday-skip/plan.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-holiday-skip/handoff.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-holiday-skip/review.md`

**Steps:**
- Scope를 explicit skip date gate로 제한한다.
- external holiday calendar fetch와 actual scheduler activation은 제외한다.
- 검증 명령을 고정한다.

### Task 2: Wrapper Skip Gate

**Files:**
- Modify: `scripts/run_portfolio_remediation_daily_scheduler.sh`

**Steps:**
- `PORTFOLIO_REMEDIATION_RUN_DATE`를 optional로 추가한다.
- 기본 run date는 `America/New_York` 기준 today로 계산한다.
- `PORTFOLIO_REMEDIATION_SKIP_DATES`를 comma/space separated ISO date list로 해석한다.
- run date가 skip list에 포함되면 skip JSON artifact와 stderr log를 생성하고 artifact path를 stdout으로 출력한다.
- skip path에서는 `portfolio-remediation-daily-run`을 호출하지 않는다.
- preflight output에 `run_date`, `skip_dates`, `would_skip`을 포함한다.

### Task 3: Verification

**Files:**
- Create: `scripts/verify_portfolio_remediation_scheduler_holiday_skip.sh`
- Modify: `scripts/verify_portfolio_remediation_scheduler_activation.sh`

**Steps:**
- wrapper syntax를 검증한다.
- skip date hit가 invalid DB command에서도 성공하는지 검증한다.
- skip JSON artifact와 stderr log가 생성되는지 검증한다.
- skip payload가 `portfolio_remediation_scheduler_skip`, `status=skipped`, run date, as-of date, reason을 포함하는지 검증한다.
- activation preflight가 새 payload field를 검증하도록 갱신한다.

### Task 4: Docs

**Files:**
- Create: `docs/portfolio-remediation-scheduler-holiday-skip.md`
- Modify: `README.md`
- Modify: `docs/portfolio-remediation-scheduler-contract.md`
- Modify: `docs/portfolio-remediation-scheduler-activation.md`
- Modify: `docs/portfolio-remediation-scheduler-env-readiness.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-holiday-skip/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-holiday-skip/review.md`

**Steps:**
- explicit skip dates 방식과 boundary를 문서화한다.
- external holiday calendar sync가 아직 없다는 점을 명시한다.
- verification evidence를 handoff/review에 남긴다.
