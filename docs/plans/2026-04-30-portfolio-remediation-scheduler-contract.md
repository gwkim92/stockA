# Portfolio Remediation Scheduler Contract Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 실제 scheduler를 켜기 전에 `portfolio-remediation-daily-run`의 실행 주기, 실패 알림, artifact 저장, retry/rollback 정책을 문서와 검증 스크립트로 고정한다.

**Architecture:** 이번 단계는 host scheduler, cron, hosted automation을 활성화하지 않는다. 대신 scheduler-ready contract를 만들고, 운영자가 수동 또는 외부 scheduler에서 호출할 command template과 안전 경계를 명시한다. 검증은 docs completeness와 no-activation boundary를 repo-local script로 확인한다.

**Tech Stack:** Markdown task harness, Bash verification script, existing `portfolio-remediation-daily-run` CLI contract.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-scheduler-contract/contract.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-contract/plan.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-contract/handoff.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-contract/review.md`
- Create: `docs/tasks/portfolio-remediation-scheduler-contract/loop_contract.md`

**Steps:**
- Scope를 scheduler activation 전 contract로 제한한다.
- 실제 automation 활성화, cron install, hosted automation 생성은 제외한다.
- 실행 주기, artifact 저장, alert, retry, rollback 기준을 필수 완료 조건으로 적는다.

### Task 2: Scheduler Contract Docs

**Files:**
- Create: `docs/portfolio-remediation-scheduler-contract.md`
- Modify: `docs/portfolio-remediation-daily-automation.md`

**Steps:**
- daily runner 호출 command template을 적는다.
- proposed cadence는 `America/New_York` 기준 market close 이후 daily로 적는다.
- artifact root, stdout/stderr capture, JSON summary 보존 규칙을 적는다.
- failure alert, retry, rollback policy를 적는다.
- activation checklist를 별도로 적고, 아직 활성화하지 않았음을 명시한다.

### Task 3: Verification Script

**Files:**
- Create: `scripts/verify_portfolio_remediation_scheduler_contract.sh`

**Steps:**
- script syntax 검증 대상이 되도록 bash script를 만든다.
- required docs가 모두 있는지 확인한다.
- required keywords가 docs에 있는지 확인한다.
- 실제 scheduler activation file을 만들지 않았음을 확인한다.

### Task 4: Project Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-contract/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-scheduler-contract/review.md`

**Steps:**
- README에 scheduler contract 문서와 verify script를 추가한다.
- verification plan에 scheduler contract verify를 추가한다.
- final verification evidence를 handoff/review에 남긴다.
