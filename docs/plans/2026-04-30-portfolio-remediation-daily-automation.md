# Portfolio Remediation Daily Automation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** daily portfolio review 운영에서 `portfolio-review-bootstrap`, `portfolio-remediation-ticket-bootstrap`, `portfolio-remediation-ticket-report`를 한 번에 실행하는 deterministic runner를 추가한다.

**Architecture:** 새 runner는 기존 검증된 기능을 조합만 한다. 자체 top-level `ops.pipeline_run`을 남기고, 하위 step도 기존 runner의 pipeline provenance를 그대로 남긴다. Ticket status update는 자동 실행하지 않고 운영자가 report를 본 뒤 별도 lifecycle command로 처리한다.

**Tech Stack:** Python stdlib, argparse CLI, Postgres SQL through existing psql executor, Docker verification script.

---

### Task 1: Harness And Automation Contract

**Files:**
- Create: `docs/tasks/portfolio-remediation-daily-automation/contract.md`
- Create: `docs/tasks/portfolio-remediation-daily-automation/plan.md`
- Create: `docs/tasks/portfolio-remediation-daily-automation/handoff.md`
- Create: `docs/tasks/portfolio-remediation-daily-automation/review.md`
- Create: `docs/tasks/portfolio-remediation-daily-automation/loop_contract.md`

**Steps:**
- Scope를 daily runner로 제한한다.
- 실제 host scheduler 활성화와 실거래 자동화는 제외한다.
- 반복 작업, keep/discard 기준, 로그/metric 기준을 `loop_contract.md`에 적는다.

### Task 2: Daily Runner Module

**Files:**
- Create: `src/stockanalysis/signal/portfolio_remediation_daily.py`
- Test: `tests/test_portfolio_remediation_daily.py`

**Steps:**
- `run_portfolio_remediation_daily_automation`을 추가한다.
- top-level pipeline name은 `portfolio_remediation_daily_automation`으로 한다.
- 순서는 review bootstrap, ticket bootstrap, ticket report다.
- `ticket_limit <= 0`을 거부한다.
- 실패 시 top-level run을 failed로 표시한다.

### Task 3: CLI

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Test: `tests/test_ingest_cli.py`

**Steps:**
- `portfolio-remediation-daily-run` command를 추가한다.
- args: `--portfolio-name`, `--as-of-date`, `--strategy-name`, `--horizon-type`, `--universe-version`
- optional args: `--market-code`, `--review-version`, `--review-source`, `--coverage-measurement-end-date`, `--ticket-limit`, `--ticket-status`
- JSON summary를 출력한다.

### Task 4: Integration Verify

**Files:**
- Create: `scripts/verify_portfolio_remediation_daily_automation.sh`

**Steps:**
- Docker Postgres에서 prerequisite pipeline을 준비한다.
- `portfolio-remediation-daily-run`을 실행한다.
- summary에서 review item 2건, BABA open ticket 1건, top-level run 성공을 확인한다.

### Task 5: Docs

**Files:**
- Create: `docs/portfolio-remediation-daily-automation.md`
- Modify: `README.md`
- Modify: `docs/portfolio-remediation-ticket-update.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-daily-automation/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-daily-automation/review.md`

**Steps:**
- 운영 순서와 boundary를 문서화한다.
- verification evidence를 handoff/review에 남긴다.
