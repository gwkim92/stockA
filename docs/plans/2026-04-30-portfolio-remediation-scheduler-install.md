# Portfolio Remediation Scheduler Install Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** macOS launchd가 호출할 수 있는 scheduler install artifact를 repo 안에 추가하되, 기본 검증은 dry-run으로 유지한다.

**Architecture:** 실제 scheduler 설치는 `scripts/install_portfolio_remediation_scheduler.sh --install`을 명시해야만 수행한다. 기본 `--dry-run`은 launchd plist를 artifact 경로에 렌더링하고, env file path, wrapper path, schedule, working directory만 검증한다. 이번 검증에서는 host LaunchAgents에 쓰지 않는다.

**Tech Stack:** Bash install script, launchd plist XML, Markdown task harness.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-scheduler-install/contract.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-install/plan.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-install/handoff.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-install/review.md`

**Steps:**
- Scope를 launchd install artifact와 dry-run verification으로 제한한다.
- 실제 host install은 검증에서 실행하지 않는다.
- alert destination은 local artifact failure marker로 둔다.
- holiday skip rule은 weekday-only plus holiday defer로 명시한다.

### Task 2: Install Script

**Files:**
- Create: `scripts/install_portfolio_remediation_scheduler.sh`

**Steps:**
- `--dry-run` 기본 모드를 구현한다.
- `--install` 명시 모드를 구현한다.
- required args/env: env file path, artifact root, label, schedule hour/minute.
- rendered plist를 artifact root 아래에 저장한다.
- `--install`일 때만 `~/Library/LaunchAgents`에 copy하고 `launchctl bootstrap` instructions를 출력한다.

### Task 3: Verification

**Files:**
- Create: `scripts/verify_portfolio_remediation_scheduler_install.sh`
- Modify: `scripts/verify_portfolio_remediation_scheduler_contract.sh`
- Modify: `scripts/verify_portfolio_remediation_scheduler_activation.sh`

**Steps:**
- install script syntax를 확인한다.
- temp env file과 temp artifact root로 dry-run을 실행한다.
- rendered plist가 wrapper, env file, schedule, label을 포함하는지 확인한다.
- install mode를 실행하지 않고 no-host-install boundary를 확인한다.
- 기존 no-activation verify는 repo-local install script 존재를 허용하도록 갱신한다.

### Task 4: Docs

**Files:**
- Create: `docs/portfolio-remediation-scheduler-install.md`
- Modify: `README.md`
- Modify: `docs/portfolio-remediation-scheduler-activation.md`
- Modify: `docs/portfolio-remediation-scheduler-contract.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-install/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-install/review.md`

**Steps:**
- dry-run/install 사용법과 boundaries를 문서화한다.
- final verification evidence를 handoff/review에 남긴다.
