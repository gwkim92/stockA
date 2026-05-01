# Portfolio Outcome Coverage Report Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Attribution에서 제외되는 portfolio positions를 식별하는 read-only coverage report를 추가한다.

**Architecture:** `portfolio.position_snapshot`을 기준으로 linked thesis와 `performance.thesis_outcome`을 left join해 position별 coverage status를 만든다. DB schema는 변경하지 않고, CLI가 JSON summary를 출력한다.

**Tech Stack:** Python stdlib, argparse CLI, Postgres SQL, existing psql executor, Docker verification script.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-outcome-coverage-report/contract.md`
- Create: `docs/tasks/portfolio-outcome-coverage-report/plan.md`
- Create: `docs/tasks/portfolio-outcome-coverage-report/handoff.md`
- Create: `docs/tasks/portfolio-outcome-coverage-report/review.md`

**Steps:**
- read-only report scope와 mutable surface를 문서화한다.
- completion criteria와 verification commands를 명시한다.

### Task 2: Coverage Report Module

**Files:**
- Create: `src/stockanalysis/performance/coverage.py`
- Test: `tests/test_portfolio_outcome_coverage_report.py`

**Steps:**
- `PortfolioOutcomeCoverageRow` dataclass를 추가한다.
- `render_portfolio_outcome_coverage_lookup_sql`을 추가한다.
- `load_portfolio_outcome_coverage_rows`를 추가한다.
- `build_portfolio_outcome_coverage_report`로 count/weight/cash/row summary를 만든다.

### Task 3: CLI

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Test: `tests/test_ingest_cli.py`

**Steps:**
- `portfolio-outcome-coverage-report` command를 추가한다.
- args: `--portfolio-name`, `--snapshot-date`, `--measurement-end-date`
- JSON summary를 출력한다.

### Task 4: Fixtures And Integration Verify

**Files:**
- Create: `tests/fixtures/portfolio_positions_long_term_paper_with_gap.csv`
- Create: `scripts/verify_portfolio_outcome_coverage_report.sh`

**Steps:**
- fixture에 AAPL covered position과 BABA missing thesis position을 둔다.
- Docker verify에서 outcome을 만든 뒤 coverage report를 실행한다.
- DB query로 covered/missing thesis count와 weight를 확인한다.

### Task 5: Docs

**Files:**
- Create: `docs/portfolio-outcome-coverage-report.md`
- Modify: `README.md`
- Modify: `docs/portfolio-attribution-bootstrap.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-outcome-coverage-report/handoff.md`
- Modify: `docs/tasks/portfolio-outcome-coverage-report/review.md`

**Steps:**
- coverage status definition과 CLI 사용법을 문서화한다.
- verification evidence를 handoff/review에 남긴다.
