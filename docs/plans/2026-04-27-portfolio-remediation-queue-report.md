# Portfolio Remediation Queue Report Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Portfolio review attention items를 remediation queue JSON으로 변환하는 read-only CLI를 추가한다.

**Architecture:** `portfolio.review`, `portfolio.review_item`, `portfolio.portfolio`, `ref.instrument`, `ops.pipeline_run`을 조합해 조치가 필요한 review item만 조회한다. Review action을 deterministic remediation type과 suggested runner로 매핑하며, DB schema와 review action rule은 변경하지 않는다.

**Tech Stack:** Python stdlib, argparse CLI, Postgres SQL, existing psql executor, Docker verification script.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-remediation-queue-report/contract.md`
- Create: `docs/tasks/portfolio-remediation-queue-report/plan.md`
- Create: `docs/tasks/portfolio-remediation-queue-report/handoff.md`
- Create: `docs/tasks/portfolio-remediation-queue-report/review.md`

**Steps:**
- read-only remediation queue scope와 mutable surface를 문서화한다.
- completion criteria와 verification commands를 명시한다.

### Task 2: Queue Report Module

**Files:**
- Create: `src/stockanalysis/signal/portfolio_remediation_queue.py`
- Test: `tests/test_portfolio_remediation_queue.py`

**Steps:**
- `load_portfolio_remediation_queue`를 추가한다.
- `render_portfolio_remediation_queue_sql`을 추가한다.
- `limit <= 0`을 거부한다.
- action을 remediation type과 suggested runner로 매핑한다.
- optional `review_source`, `action`, `remediation_type` filter를 SQL에 반영한다.

### Task 3: CLI

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Test: `tests/test_ingest_cli.py`

**Steps:**
- `portfolio-remediation-queue` command를 추가한다.
- args: `--portfolio-name`, `--limit`, `--review-source`, `--action`, `--remediation-type`
- JSON summary를 출력한다.

### Task 4: Integration Verify

**Files:**
- Create: `scripts/verify_portfolio_remediation_queue_report.sh`

**Steps:**
- Docker Postgres에서 coverage-gated portfolio review를 만든다.
- `portfolio-remediation-queue` JSON을 생성한다.
- BABA `needs_thesis_review`가 `thesis_remediation` item으로 출력되는지 확인한다.

### Task 5: Docs

**Files:**
- Create: `docs/portfolio-remediation-queue-report.md`
- Modify: `README.md`
- Modify: `docs/portfolio-review-run-history-report.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-remediation-queue-report/handoff.md`
- Modify: `docs/tasks/portfolio-remediation-queue-report/review.md`

**Steps:**
- queue shape와 CLI 사용법을 문서화한다.
- verification evidence를 handoff/review에 남긴다.
