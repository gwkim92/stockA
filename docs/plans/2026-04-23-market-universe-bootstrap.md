# Market Universe Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `SEC company_tickers_exchange.json`을 기반으로 미국 상장 universe를 canonical `ref.issuer`, `ref.instrument`에 bootstrap하는 `market-universe-bootstrap` 경로를 만든다.

**Architecture:** `sec` source adapter에 `company_tickers_exchange` dataset을 추가하고, market universe runner가 SEC payload를 정규화한 뒤 supported exchange만 필터링해서 canonical reference tables에 upsert한다. 이 단계에서는 `Nasdaq`, `NYSE`만 지원하고 `OTC`, `CBOE`, missing exchange는 skip한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: 범위와 task 문서 고정

**Files:**
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-universe-bootstrap/contract.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-universe-bootstrap/plan.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-universe-bootstrap/handoff.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-universe-bootstrap/review.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-batch-ingest/handoff.md`

**Step 1: 작업 범위를 고정한다**

- source는 SEC `company_tickers_exchange`만 사용
- supported exchange는 `Nasdaq`, `NYSE`만 허용
- output은 canonical `ref.issuer`, `ref.instrument` upsert와 summary까지만 다룸

**Step 2: 검증 경로를 적는다**

- `bash /Users/woody/ai/stockanalysis/scripts/verify_market_universe_bootstrap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-universe-bootstrap`

### Task 2: source adapter, runner, CLI 구현

**Files:**
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sources/sec.py`
- Create: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/market/universe.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/cli.py`
- Create: `/Users/woody/ai/stockanalysis/tests/test_market_universe.py`
- Modify: `/Users/woody/ai/stockanalysis/tests/test_ingest_cli.py`

**Step 1: failing test를 쓴다**

- SEC payload normalization
- unsupported exchange skip
- `ref.issuer`/`ref.instrument` upsert SQL
- CLI summary

**Step 2: minimal runner를 구현한다**

- fixture/live payload loading
- exchange mapping과 filter
- pipeline run 기록
- canonical reference upsert

### Task 3: fixture, integration verify, 운영 문서 추가

**Files:**
- Create: `/Users/woody/ai/stockanalysis/tests/fixtures/sec_company_tickers_exchange_sample.json`
- Create: `/Users/woody/ai/stockanalysis/scripts/verify_market_universe_bootstrap.sh`
- Create: `/Users/woody/ai/stockanalysis/docs/market-universe-bootstrap.md`
- Modify: `/Users/woody/ai/stockanalysis/README.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/verification-plan.md`

**Step 1: sample fixture를 추가한다**

- `AAPL`, `MSFT`, unsupported `OTC` row 포함

**Step 2: docker verify를 추가한다**

- migration + seed
- fixture 기반 `market-universe-bootstrap`
- issuer/instrument row count와 symbol 존재, succeeded pipeline run 확인

**Step 3: 운영 문서를 마무리한다**

- CLI usage
- supported exchange mapping
- current limitations
