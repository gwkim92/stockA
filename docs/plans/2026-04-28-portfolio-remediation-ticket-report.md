# Portfolio Remediation Ticket Report Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `portfolio.remediation_ticket`의 open/in_progress/resolved/ignored ticket을 운영자가 조회할 수 있는 read-only CLI를 추가한다.

**Architecture:** 기존 persistent ticket table을 source of truth로 사용하고, portfolio/review/instrument/pipeline metadata를 join해 JSON report를 만든다. Schema, review rule, recommendation/thesis/performance 산식은 변경하지 않는다.

**Tech Stack:** Python stdlib, argparse CLI, Postgres SQL, existing psql executor, Docker verification script.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-ticket-report/contract.md`
- Create: `docs/tasks/portfolio-remediation-ticket-report/plan.md`
- Create: `docs/tasks/portfolio-remediation-ticket-report/handoff.md`
- Create: `docs/tasks/portfolio-remediation-ticket-report/review.md`

**Steps:**
- Scope를 read-only ticket report로 제한한다.
- mutable surface와 금지 범위를 명시한다.
- 검증 명령을 고정한다.

### Task 2: Report Module

**Files:**
- Modify: `src/stockanalysis/signal/portfolio_remediation_ticket.py`
- Test: `tests/test_portfolio_remediation_ticket.py`

**Steps:**
- `load_portfolio_remediation_ticket_report`를 추가한다.
- `render_portfolio_remediation_ticket_report_sql`을 추가한다.
- `limit <= 0`을 거부한다.
- optional `status`, `action`, `remediation_type`, `suggested_runner` filter를 지원한다.

### Task 3: CLI

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Test: `tests/test_ingest_cli.py`

**Steps:**
- `portfolio-remediation-ticket-report` command를 추가한다.
- args: `--portfolio-name`, `--limit`, `--status`, `--action`, `--remediation-type`, `--suggested-runner`
- `--status all`은 status filter를 제거한다.
- JSON report를 출력한다.

### Task 4: Integration Verify

**Files:**
- Create: `scripts/verify_portfolio_remediation_ticket_report.sh`

**Steps:**
- Docker Postgres에서 coverage-gated portfolio review를 만든다.
- `portfolio-remediation-ticket-bootstrap`으로 BABA ticket을 생성한다.
- `portfolio-remediation-ticket-report`로 open ticket을 조회한다.
- BABA `needs_thesis_review` ticket 1건과 status/remediation/suggested runner를 확인한다.

### Task 5: Docs

**Files:**
- Create: `docs/portfolio-remediation-ticket-report.md`
- Modify: `README.md`
- Modify: `docs/portfolio-remediation-ticket-bootstrap.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-ticket-report/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-ticket-report/review.md`

**Steps:**
- report output shape와 CLI 사용법을 문서화한다.
- verification evidence를 handoff/review에 남긴다.
