# Long Horizon Outcome Runner Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 하나의 recommendation batch에 대해 여러 measurement horizon의 performance outcome을 저장하는 batch runner를 만든다.

**Architecture:** 기존 `run_performance_outcome_bootstrap`은 단일 `measurement_end_date`를 처리한다. 새 runner는 반복 측정일 또는 horizon day를 받아 정렬/중복 제거한 뒤 기존 단일 runner를 순차 실행하고, 결과를 aggregate summary로 반환한다. DB schema는 이미 `(recommendation_id, measurement_end_date)` unique index로 여러 horizon 저장을 지원하므로 schema 변경은 하지 않는다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: 작업 경계 고정

**Files:**
- Create: `docs/tasks/long-horizon-outcome-runner/contract.md`
- Create: `docs/tasks/long-horizon-outcome-runner/plan.md`
- Create: `docs/tasks/long-horizon-outcome-runner/handoff.md`
- Create: `docs/tasks/long-horizon-outcome-runner/review.md`

**Steps:**
- 범위는 multi-horizon outcome scheduling으로 제한한다.
- recommendation scoring, thesis generation, portfolio review, schema 변경은 하지 않는다.
- horizon day는 `as_of_date + days`로 measurement date를 만든다.

### Task 2: batch runner 구현

**Files:**
- Modify: `src/stockanalysis/performance/outcome.py`
- Modify: `tests/test_performance_outcome_bootstrap.py`

**Steps:**
- `resolve_performance_measurement_dates(as_of_date, measurement_end_dates, horizon_days)`를 추가한다.
- repeated explicit dates와 horizon day를 함께 받되 중복은 제거하고 오름차순 정렬한다.
- horizon day는 0보다 커야 한다.
- `run_performance_outcome_batch_bootstrap`을 추가해 각 measurement date마다 `run_performance_outcome_bootstrap`을 호출한다.
- summary에는 requested measurement dates, succeeded count, total outcome counts, aggregate label counts, per-date results를 담는다.

### Task 3: CLI 추가

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Modify: `tests/test_ingest_cli.py`

**Steps:**
- `performance-outcome-batch-bootstrap` command를 추가한다.
- args:
  - `--as-of-date`
  - repeated `--measurement-end-date`
  - repeated `--horizon-day`
  - `--strategy-name`
  - `--horizon-type`
  - `--universe-version`
  - `--market-code`
  - `--outcome-version`
- explicit measurement date나 horizon day 중 하나 이상이 없으면 에러를 반환한다.

### Task 4: long horizon fixture와 Docker verify 확장

**Files:**
- Modify: `tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json`
- Modify: `tests/fixtures/alpha_vantage_daily_adjusted_SPY.json`
- Modify: `scripts/verify_performance_outcome_bootstrap.sh`

**Steps:**
- AAPL 2024-12-02 adjusted close `245.2010`를 추가해 long horizon absolute return `0.100000`을 만든다.
- SPY 2024-12-02 adjusted close `592.8000`을 추가해 long horizon benchmark return `0.040000`을 만든다.
- batch CLI를 `--measurement-end-date 2024-11-04 --measurement-end-date 2024-12-02`로 실행한다.
- DB assertion은 recommendation/thesis outcome 2건, short horizon alpha `0.005000`, long horizon alpha `0.060000`을 확인한다.

### Task 5: docs와 verification

**Files:**
- Modify: `docs/performance-outcome-bootstrap.md`
- Modify: `docs/verification-plan.md`
- Modify: `README.md`
- Modify: `docs/tasks/long-horizon-outcome-runner/handoff.md`
- Modify: `docs/tasks/long-horizon-outcome-runner/review.md`

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_performance_outcome_bootstrap.sh
bash scripts/verify_performance_outcome_bootstrap.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task long-horizon-outcome-runner
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
