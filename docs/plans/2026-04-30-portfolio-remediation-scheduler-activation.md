# Portfolio Remediation Scheduler Activation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 실제 scheduler가 호출할 repo-local runtime wrapper와 preflight 검증을 추가해 `portfolio-remediation-daily-run` activation 준비 상태를 만든다.

**Architecture:** 이번 단계는 cron/launchd/hosted automation을 설치하지 않는다. 대신 scheduler가 나중에 호출할 단일 wrapper를 만들고, wrapper가 required env, artifact root, stdout/stderr capture, JSON validation을 담당하게 한다. 검증은 preflight-only mode와 no-scheduler-install boundary를 확인한다.

**Tech Stack:** Bash wrapper, Python stdlib JSON validation, Markdown task harness, existing `portfolio-remediation-daily-run` CLI.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-scheduler-activation/contract.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-activation/plan.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-activation/handoff.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-activation/review.md`

**Steps:**
- Scope를 activation-preflight와 runtime wrapper로 제한한다.
- 실제 scheduler install, hosted automation, secrets 변경은 제외한다.
- 검증 명령을 고정한다.

### Task 2: Runtime Wrapper

**Files:**
- Create: `scripts/run_portfolio_remediation_daily_scheduler.sh`

**Steps:**
- `--preflight-only` mode를 지원한다.
- required env를 검증한다.
- artifact root를 만들고 writable 여부를 확인한다.
- run mode에서는 `portfolio-remediation-daily-run`을 실행해 stdout JSON과 stderr log를 artifact로 저장한다.
- stdout JSON의 `report_name`을 검증한다.

### Task 3: Verification Script

**Files:**
- Create: `scripts/verify_portfolio_remediation_scheduler_activation.sh`

**Steps:**
- wrapper와 verify script syntax를 확인한다.
- temp artifact root에서 `--preflight-only`를 실행한다.
- required env 누락 시 wrapper가 실패하는지 확인한다.
- cron/launchd/GitHub Actions scheduler artifact가 없는지 확인한다.

### Task 4: Docs

**Files:**
- Create: `docs/portfolio-remediation-scheduler-activation.md`
- Modify: `docs/portfolio-remediation-scheduler-contract.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-activation/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-activation/review.md`

**Steps:**
- wrapper env와 artifact naming을 문서화한다.
- actual scheduler activation은 아직 별도 승인 대상임을 명시한다.
- verification evidence를 handoff/review에 남긴다.
