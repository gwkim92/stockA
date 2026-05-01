# Portfolio Remediation Ticket Update Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `portfolio.remediation_ticket`의 status를 `open`, `in_progress`, `resolved`, `ignored`로 변경하는 CLI를 추가한다.

**Architecture:** 기존 ticket table의 `status`, `updated_at`, `resolved_at` 필드만 갱신한다. Update 실행 자체는 `ops.pipeline_run`으로 남기지만, ticket의 `source_run_id`는 ticket을 마지막으로 관측한 bootstrap provenance로 유지한다.

**Tech Stack:** Python stdlib, argparse CLI, Postgres SQL, existing psql executor, Docker verification script.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-ticket-update/contract.md`
- Create: `docs/tasks/portfolio-remediation-ticket-update/plan.md`
- Create: `docs/tasks/portfolio-remediation-ticket-update/handoff.md`
- Create: `docs/tasks/portfolio-remediation-ticket-update/review.md`

**Steps:**
- Scope를 ticket lifecycle status update로 제한한다.
- DB schema 변경 없음과 금지 범위를 명시한다.
- 검증 명령을 고정한다.

### Task 2: Update Module

**Files:**
- Modify: `src/stockanalysis/signal/portfolio_remediation_ticket.py`
- Test: `tests/test_portfolio_remediation_ticket.py`

**Steps:**
- `run_portfolio_remediation_ticket_update`를 추가한다.
- `render_portfolio_remediation_ticket_update_sql`을 추가한다.
- `ticket_id <= 0`과 unsupported status를 거부한다.
- `resolved`/`ignored`는 `resolved_at = now()`로 저장한다.
- `open`/`in_progress`는 `resolved_at = null`로 저장한다.
- ticket이 없으면 runner가 실패로 처리한다.

### Task 3: CLI

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Test: `tests/test_ingest_cli.py`

**Steps:**
- `portfolio-remediation-ticket-update` command를 추가한다.
- args: `--portfolio-name`, `--ticket-id`, `--status`
- status choices: `open`, `in_progress`, `resolved`, `ignored`
- JSON summary를 출력한다.

### Task 4: Integration Verify

**Files:**
- Create: `scripts/verify_portfolio_remediation_ticket_update.sh`

**Steps:**
- Docker Postgres에서 coverage-gated portfolio review를 만든다.
- `portfolio-remediation-ticket-bootstrap`으로 BABA ticket을 생성한다.
- `portfolio-remediation-ticket-report`로 ticket id를 찾는다.
- `portfolio-remediation-ticket-update --status resolved`를 실행한다.
- resolved report에서 BABA ticket status와 non-null `resolved_at`을 확인한다.

### Task 5: Docs

**Files:**
- Create: `docs/portfolio-remediation-ticket-update.md`
- Modify: `README.md`
- Modify: `docs/portfolio-remediation-ticket-report.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-ticket-update/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-ticket-update/review.md`

**Steps:**
- lifecycle command와 boundary를 문서화한다.
- verification evidence를 handoff/review에 남긴다.
