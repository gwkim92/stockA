# Benchmark Outcome Alpha Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** benchmark ETF price가 있는 경우 recommendation/thesis outcome에 benchmark return, alpha, outperform/underperform/inline label이 저장되는지 검증한다.

**Architecture:** 기존 `performance-outcome-bootstrap` runner는 이미 thesis `benchmark_code`와 동일한 canonical instrument price를 읽는다. 이 작업은 SPY를 데이터 수집기 경로로 canonical universe와 price bar에 넣는 fixture를 추가하고, unit/Docker 검증을 alpha 경로까지 확장한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: 작업 경계 고정

**Files:**
- Create: `docs/tasks/benchmark-outcome-alpha/contract.md`
- Create: `docs/tasks/benchmark-outcome-alpha/plan.md`
- Create: `docs/tasks/benchmark-outcome-alpha/handoff.md`
- Create: `docs/tasks/benchmark-outcome-alpha/review.md`

**Steps:**
- 범위는 benchmark fixture와 outcome alpha 검증으로 제한한다.
- 추천 점수, thesis 생성 규칙, portfolio review, 실거래 PnL은 바꾸지 않는다.
- benchmark는 수동 DB insert가 아니라 기존 `market-universe-bootstrap`, `market-price-upsert` 경로로 적재한다.

### Task 2: fixture와 unit test 확장

**Files:**
- Create: `tests/fixtures/sec_company_tickers_exchange_with_benchmark_sample.json`
- Create: `tests/fixtures/alpha_vantage_daily_adjusted_SPY.json`
- Modify: `tests/test_performance_outcome_bootstrap.py`

**Steps:**
- SEC universe fixture에 기존 AAPL/BABA/BAESY와 SPY row를 추가한다.
- SPY daily adjusted fixture는 2024-11-01 `570.0000`, 2024-11-04 `572.8500`으로 만들어 benchmark return `0.005000`을 만든다.
- AAPL return `0.010000`과 SPY benchmark return `0.005000`으로 alpha `0.005000`, label `outperform`을 검증하는 unit test를 추가한다.
- SQL rendering test가 benchmark return, alpha, outperform label을 포함하는지 확인한다.

### Task 3: Docker verify 확장

**Files:**
- Modify: `scripts/verify_performance_outcome_bootstrap.sh`

**Steps:**
- performance verify에서 benchmark 포함 universe fixture를 사용한다.
- backfill에서 SPY fixture도 적재되게 한다.
- outcome fixture로 AAPL 2024-11-04 가격을 갱신한다.
- DB assertion을 benchmark 경로 기준으로 바꾼다.
- 기대값은 AAPL recommendation outcome 1건, thesis outcome 1건, `absolute_return_pct = 0.010000`, `benchmark_return_pct = 0.005000`, `alpha_pct = 0.005000`, label `outperform`, thesis status `working`, success grade `pass`다.

### Task 4: docs와 handoff 갱신

**Files:**
- Modify: `docs/performance-outcome-bootstrap.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/performance-outcome-bootstrap/handoff.md`
- Modify: `docs/tasks/benchmark-outcome-alpha/handoff.md`
- Modify: `docs/tasks/benchmark-outcome-alpha/review.md`

**Steps:**
- benchmark가 있는 검증 경로가 완료됐음을 문서화한다.
- 남은 리스크를 장기 horizon, 실거래 PnL, portfolio attribution으로 좁힌다.

### Task 5: verification

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_performance_outcome_bootstrap.sh
bash scripts/verify_performance_outcome_bootstrap.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task benchmark-outcome-alpha
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
