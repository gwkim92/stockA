# Portfolio Remediation Ticket Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `portfolio-remediation-queue` 결과를 persistent `portfolio.remediation_ticket` row로 저장하는 bootstrap CLI를 추가한다.

**Architecture:** 기존 read-only queue mapping을 재사용하되, ticket 저장은 별도 migration과 bootstrap runner로 분리한다. Ticket은 review item의 현재 조치 필요 상태를 운영 큐로 남기며, remediation 자동 실행이나 trading action은 만들지 않는다.

**Tech Stack:** Python stdlib, argparse CLI, Postgres SQL, existing psql executor, Docker verification script.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-ticket-bootstrap/contract.md`
- Create: `docs/tasks/portfolio-remediation-ticket-bootstrap/plan.md`
- Create: `docs/tasks/portfolio-remediation-ticket-bootstrap/handoff.md`
- Create: `docs/tasks/portfolio-remediation-ticket-bootstrap/review.md`

**Steps:**
- Scope를 persistent ticket bootstrap으로 제한한다.
- DB schema 변경 범위와 금지 범위를 명시한다.
- 검증 명령을 고정한다.

### Task 2: Migration

**Files:**
- Create: `db/migrations/0012_portfolio_remediation_ticket.sql`
- Modify: `docs/db-schema-design.md`

**Steps:**
- `portfolio.remediation_ticket` table을 추가한다.
- unique identity는 `(portfolio_review_id, instrument_id, action, remediation_type)`로 둔다.
- status, suggested runner, priority, reason, source_run_id, opened/updated/last_seen timestamp를 저장한다.
- review item rerun 시 기존 ticket이 cascade 삭제되지 않도록 `portfolio.review_item` FK는 두지 않는다.

### Task 3: Bootstrap Module

**Files:**
- Create: `src/stockanalysis/signal/portfolio_remediation_ticket.py`
- Test: `tests/test_portfolio_remediation_ticket.py`

**Steps:**
- `render_portfolio_remediation_ticket_bootstrap_sql`을 추가한다.
- `run_portfolio_remediation_ticket_bootstrap`을 추가한다.
- `limit <= 0`을 거부한다.
- pipeline run을 생성하고 성공/실패 상태를 남긴다.
- optional `review_source`, `action`, `remediation_type` filter를 지원한다.

### Task 4: CLI

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Test: `tests/test_ingest_cli.py`

**Steps:**
- `portfolio-remediation-ticket-bootstrap` command를 추가한다.
- args: `--portfolio-name`, `--limit`, `--review-source`, `--action`, `--remediation-type`
- JSON summary를 출력한다.

### Task 5: Integration Verify

**Files:**
- Create: `scripts/verify_portfolio_remediation_ticket_bootstrap.sh`

**Steps:**
- Docker Postgres에서 coverage-gated portfolio review를 만든다.
- `portfolio-remediation-ticket-bootstrap`을 실행한다.
- BABA `needs_thesis_review` ticket 1건이 `open`, `thesis_remediation`, `thesis_or_position_link_review`로 저장되는지 확인한다.
- 같은 bootstrap을 한 번 더 실행해 duplicate ticket이 생기지 않는지 확인한다.

### Task 6: Docs

**Files:**
- Create: `docs/portfolio-remediation-ticket-bootstrap.md`
- Modify: `README.md`
- Modify: `docs/portfolio-remediation-queue-report.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-ticket-bootstrap/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-ticket-bootstrap/review.md`

**Steps:**
- ticket schema와 CLI 사용법을 문서화한다.
- read-only queue와 persistent ticket의 차이를 명시한다.
- verification evidence를 handoff/review에 남긴다.
