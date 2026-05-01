# Portfolio Review Run History Report Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 최근 portfolio review 실행과 action/risk/remediation 후보를 read-only JSON으로 조회하는 운영 리포트를 추가한다.

**Architecture:** `portfolio.review`, `portfolio.review_item`, `portfolio.portfolio`, `ref.instrument`, `ops.pipeline_run`을 조합해 run history report를 만든다. DB schema는 변경하지 않고, CLI가 최근 review runs, risk counts, action counts, attention items를 JSON으로 출력한다.

**Tech Stack:** Python stdlib, argparse CLI, Postgres SQL, existing psql executor, Docker verification script.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-review-run-history-report/contract.md`
- Create: `docs/tasks/portfolio-review-run-history-report/plan.md`
- Create: `docs/tasks/portfolio-review-run-history-report/handoff.md`
- Create: `docs/tasks/portfolio-review-run-history-report/review.md`

**Steps:**
- read-only report scope와 mutable surface를 문서화한다.
- completion criteria와 verification commands를 명시한다.

### Task 2: Report Module

**Files:**
- Create: `src/stockanalysis/signal/portfolio_review_report.py`
- Test: `tests/test_portfolio_review_report.py`

**Steps:**
- `load_portfolio_review_run_history`를 추가한다.
- `render_portfolio_review_run_history_sql`을 추가한다.
- `limit <= 0`을 거부한다.
- optional `review_source`, `risk_level`, `action` filter를 SQL에 반영한다.
- report JSON에 recent reviews, action counts, risk counts, attention items를 포함한다.

### Task 3: CLI

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Test: `tests/test_ingest_cli.py`

**Steps:**
- `portfolio-review-run-history` command를 추가한다.
- args: `--portfolio-name`, `--limit`, `--review-source`, `--risk-level`, `--action`
- JSON summary를 출력한다.

### Task 4: Integration Verify

**Files:**
- Create: `scripts/verify_portfolio_review_run_history_report.sh`

**Steps:**
- Docker Postgres에서 portfolio review bootstrap과 coverage gate rerun을 실행한다.
- `portfolio-review-run-history` JSON을 생성한다.
- AAPL `monitor`, BABA `needs_thesis_review`, risk `watch`, action counts를 확인한다.

### Task 5: Docs

**Files:**
- Create: `docs/portfolio-review-run-history-report.md`
- Modify: `README.md`
- Modify: `docs/portfolio-review-bootstrap.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-review-run-history-report/handoff.md`
- Modify: `docs/tasks/portfolio-review-run-history-report/review.md`

**Steps:**
- report shape와 CLI 사용법을 문서화한다.
- verification evidence를 handoff/review에 남긴다.
