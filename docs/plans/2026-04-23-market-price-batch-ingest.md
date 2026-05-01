# Market Price Batch Ingest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 여러 종목의 Alpha Vantage daily adjusted fixture/live payload를 한 번에 canonical `market.daily_price_bar`에 적재하는 `market-price-batch-upsert` 경로를 만든다.

**Architecture:** 기존 `run_market_price_upsert` runner를 재사용하고, batch wrapper가 repeatable symbol list와 optional fixture directory resolution만 추가한다. 각 symbol은 기존과 동일하게 개별 `pipeline_run`을 남기고, batch는 aggregate summary만 반환한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: 범위와 task 문서 고정

**Files:**
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-batch-ingest/contract.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-batch-ingest/plan.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-batch-ingest/handoff.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-batch-ingest/review.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-ingest/handoff.md`

**Step 1: 작업 범위를 고정한다**

- repeatable symbol list only
- optional fixture directory mode
- per-symbol pipeline run 유지

**Step 2: 검증 경로를 적는다**

- `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_batch_ingest.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-batch-ingest`

### Task 2: batch runner와 CLI 구현

**Files:**
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/market/price.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/cli.py`
- Modify: `/Users/woody/ai/stockanalysis/tests/test_market_price.py`
- Modify: `/Users/woody/ai/stockanalysis/tests/test_ingest_cli.py`

**Step 1: failing test를 쓴다**

- fixture directory resolution
- batch success/failure summary
- batch CLI summary

**Step 2: minimal batch runner를 구현한다**

- repeatable symbol 처리
- fixture file name convention
- continue-on-error summary

### Task 3: second fixture와 integration verify 추가

**Files:**
- Create: `/Users/woody/ai/stockanalysis/tests/fixtures/alpha_vantage_daily_adjusted_MSFT.json`
- Create: `/Users/woody/ai/stockanalysis/scripts/verify_market_price_batch_ingest.sh`
- Create: `/Users/woody/ai/stockanalysis/docs/market-price-batch-ingest.md`
- Modify: `/Users/woody/ai/stockanalysis/README.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/verification-plan.md`

**Step 1: second symbol fixture를 추가한다**

- `MSFT` daily adjusted fixture

**Step 2: docker verify를 추가한다**

- canonical Apple/Microsoft issuer/instrument insert
- 2-symbol batch upsert
- bar row count와 per-symbol succeeded run count 확인

**Step 3: 운영 문서를 마무리한다**

- CLI usage
- batch summary shape
- current limits
