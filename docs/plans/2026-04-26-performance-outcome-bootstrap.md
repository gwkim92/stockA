# Performance Outcome Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** recommendation과 thesis의 사후 가격 성과를 canonical performance tables에 저장한다.

**Architecture:** recommendation batch identity와 measurement end date를 입력으로 받고, `market.daily_price_bar`에서 entry/end price를 조회해 absolute return, optional benchmark return, alpha, drawdown, outcome label을 계산한다. 결과는 `performance.recommendation_outcome`과 `performance.thesis_outcome`에 upsert한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: schema와 작업 경계 고정

**Files:**
- Create: `docs/plans/2026-04-26-performance-outcome-bootstrap.md`
- Create: `docs/tasks/performance-outcome-bootstrap/contract.md`
- Create: `docs/tasks/performance-outcome-bootstrap/plan.md`
- Create: `docs/tasks/performance-outcome-bootstrap/handoff.md`
- Create: `docs/tasks/performance-outcome-bootstrap/review.md`
- Create: `db/migrations/0010_performance_outcome.sql`

**Step 1: Fix scope**

- Include recommendation outcome and thesis outcome persistence.
- Include price-based absolute return, optional benchmark return, alpha, max drawdown, labels.
- Exclude attribution decomposition, portfolio-level attribution, live benchmark sourcing, and AI grading.

### Task 2: outcome runner 구현

**Files:**
- Create: `src/stockanalysis/performance/__init__.py`
- Create: `src/stockanalysis/performance/outcome.py`
- Create: `tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json`
- Create: `tests/test_performance_outcome_bootstrap.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add tests**

- candidate lookup SQL joins recommendation, thesis, market price entry/end bars.
- build rows computes AAPL 1.0000% return from 222.9100 to 225.1391.
- upsert SQL inserts both `performance.recommendation_outcome` and `performance.thesis_outcome`.
- runner records `ops.pipeline_run` and returns label counts.
- CLI command prints JSON summary.

**Step 2: Implement**

- Load candidates for recommendation batch identity and measurement end date.
- Entry price is latest adjusted close on or before recommendation as-of date.
- Exit price is latest adjusted close on or before measurement end date.
- Benchmark return is calculated only when benchmark instrument and price bars exist.
- Upsert recommendation and thesis outcome rows in one transaction.

### Task 3: verification과 docs

**Files:**
- Create: `scripts/verify_performance_outcome_bootstrap.sh`
- Create: `docs/performance-outcome-bootstrap.md`
- Modify: `README.md`
- Modify: `docs/db-schema-design.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/performance-outcome-bootstrap/handoff.md`
- Modify: `docs/tasks/performance-outcome-bootstrap/review.md`

**Step 1: Docker verify**

- Run full chain through `thesis-review-bootstrap`.
- Load outcome price fixture with AAPL 2024-11-04 adjusted close `225.1391`.
- Run `performance-outcome-bootstrap` for measurement end date `2024-11-04`.
- Assert recommendation outcome 1건, thesis outcome 1건, absolute return `0.010000`, outcome label `positive`, latest pipeline run status `succeeded`.

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_performance_outcome_bootstrap.sh
bash scripts/verify_performance_outcome_bootstrap.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task performance-outcome-bootstrap
if rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S; then exit 1; fi
```
