# Market Price Ingest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Alpha Vantage daily adjusted price JSON을 canonical `market.daily_price_bar`에 적재하는 첫 `market-price-ingest` 경로를 만든다.

**Architecture:** existing `alpha_vantage` source adapter를 재사용하고, `TIME_SERIES_DAILY_ADJUSTED` payload를 normalized daily bar records로 변환한 뒤 canonical instrument exact-match lookup과 `market.daily_price_bar` upsert를 수행한다. 첫 단계는 single symbol, daily bars, fixture/live dual path만 다루는 deterministic MVP로 제한한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: 범위와 task 문서 고정

**Files:**
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-ingest/contract.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-ingest/plan.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-ingest/handoff.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/market-price-ingest/review.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/tasks/sec-companyfacts-ingest/handoff.md`

**Step 1: 작업 범위를 고정한다**

- Alpha Vantage daily adjusted only
- exact-match symbol lookup
- daily_price_bar only

**Step 2: 검증 경로를 적는다**

- `bash /Users/woody/ai/stockanalysis/scripts/verify_market_price_ingest.sh`
- `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-price-ingest`

### Task 2: parser와 upsert SQL 구현

**Files:**
- Create: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/market/price.py`
- Create: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/market/__init__.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_market_price.py`

**Step 1: failing test를 쓴다**

- fixture 기반 Alpha Vantage normalize
- daily_price_bar upsert SQL
- instrument lookup by symbol

**Step 2: minimal parser를 구현한다**

- `Meta Data`
- `Time Series (Daily)`
- sorted daily bar normalize

**Step 3: minimal SQL renderer를 구현한다**

- exact-match symbol lookup
- `market.daily_price_bar` upsert

### Task 3: runner와 CLI 구현

**Files:**
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/cli.py`
- Modify: `/Users/woody/ai/stockanalysis/tests/test_ingest_cli.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_market_price.py`

**Step 1: runner failing test를 쓴다**

- pipeline run lifecycle
- CLI summary

**Step 2: minimal runner를 구현한다**

- fixture 또는 live daily_adjusted payload load
- exact-match symbol lookup
- pipeline run 생성과 daily bar upsert 실행

### Task 4: integration verify와 운영 문서 추가

**Files:**
- Create: `/Users/woody/ai/stockanalysis/tests/fixtures/alpha_vantage_daily_adjusted_AAPL.json`
- Create: `/Users/woody/ai/stockanalysis/scripts/verify_market_price_ingest.sh`
- Create: `/Users/woody/ai/stockanalysis/docs/market-price-ingest.md`
- Modify: `/Users/woody/ai/stockanalysis/README.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/verification-plan.md`

**Step 1: docker verify를 추가한다**

- canonical Apple issuer/instrument insert
- fixture 기반 price upsert
- bar row count와 adjusted close 확인

**Step 2: 운영 문서를 마무리한다**

- supported source
- current limits
- next step
