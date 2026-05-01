# Market Price Universe Backfill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** canonical `ref.instrument` universe에서 active symbol list를 읽어 `market-price-batch-upsert`를 자동 실행하는 `market-price-universe-backfill` 경로를 만든다.

**Architecture:** backfill runner가 canonical universe query로 symbol list를 읽고, 기존 `run_market_price_batch_upsert`를 재사용한다. 이 단계에서는 `market-universe-bootstrap`으로 올라간 symbol 중 `Nasdaq`/`NYSE` active instrument만 다룬다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: 범위와 task 문서 고정

**Files:**
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-universe-backfill/contract.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-universe-backfill/plan.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-universe-backfill/handoff.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-universe-backfill/review.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/tasks/market-universe-bootstrap/handoff.md`

**Step 1: 작업 범위를 고정한다**

- canonical active instrument lookup
- market price batch runner reuse
- fixture-driven backfill verify

**Step 2: 검증 경로를 적는다**

- `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_universe_backfill.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-universe-backfill`

### Task 2: symbol selection과 backfill runner 구현

**Files:**
- Create: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/market/backfill.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/cli.py`
- Create: `/Users/woody/ai/stockanalysis/tests/test_market_backfill.py`
- Modify: `/Users/woody/ai/stockanalysis/tests/test_ingest_cli.py`

**Step 1: failing test를 쓴다**

- canonical symbol lookup SQL
- limit/filter handling
- batch runner reuse
- CLI summary

**Step 2: minimal backfill runner를 구현한다**

- active instrument query
- optional exchange/limit filter
- existing `run_market_price_batch_upsert` 호출

### Task 3: second price fixture, docker verify, 운영 문서 추가

**Files:**
- Create: `/Users/woody/ai/stockanalysis/tests/fixtures/alpha_vantage_daily_adjusted_BABA.json`
- Create: `/Users/woody/ai/stockanalysis/scripts/verify_market_price_universe_backfill.sh`
- Create: `/Users/woody/ai/stockanalysis/docs/market-price-universe-backfill.md`
- Modify: `/Users/woody/ai/stockanalysis/README.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/verification-plan.md`

**Step 1: second price fixture를 추가한다**

- `BABA` daily adjusted fixture

**Step 2: docker verify를 추가한다**

- market universe bootstrap 먼저 실행
- universe backfill 실행
- per-symbol daily bar count와 pipeline run count 확인

**Step 3: 운영 문서를 마무리한다**

- CLI usage
- canonical symbol selection rule
- current limits
