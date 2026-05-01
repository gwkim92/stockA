# SEC Companyfacts Ingest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** SEC companyfacts JSON을 canonical financial schema에 적재하는 첫 `sec-companyfacts-ingest` 경로를 만든다.

**Architecture:** `companyfacts` payload에서 selected `us-gaap` USD facts만 정규화하고, `entityName` 기반 exact-match canonical instrument lookup 뒤 `market.financial_statement_period`와 `market.financial_metric_value`에 upsert한다. 첫 단계는 10-K/10-Q와 핵심 duration metrics만 다루는 deterministic MVP로 제한한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: 범위와 task 문서 고정

**Files:**
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-companyfacts-ingest/contract.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-companyfacts-ingest/plan.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-companyfacts-ingest/handoff.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/sec-companyfacts-ingest/review.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/tasks/event-instrument-impact-bootstrap/handoff.md`

**Step 1: 작업 범위를 고정한다**

- companyfacts -> canonical financial schema
- selected USD `us-gaap` metrics only
- exact-match instrument lookup

**Step 2: 검증 경로를 적는다**

- `bash /Users/woody/ai/stockanalysis/scripts/verify_sec_companyfacts_ingest.sh`
- `PYTHONPATH=/tmp/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task sec-companyfacts-ingest`

### Task 2: parser와 upsert SQL 구현

**Files:**
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/models.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/sql.py`
- Create: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/companyfacts.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_sec_companyfacts.py`

**Step 1: failing test를 쓴다**

- fixture 기반 companyfacts normalize
- selected metric filtering
- companyfacts upsert SQL

**Step 2: minimal parser를 구현한다**

- `entityName`, `cik`, `facts.us-gaap`
- 10-K/10-Q duration facts만 선택
- internal metric code로 변환

**Step 3: minimal SQL renderer를 구현한다**

- `market.financial_statement_period` upsert
- `market.financial_metric_value` upsert
- `ingest.source_document.external_document_id` 기준 optional source document linkage

### Task 3: runner와 CLI 구현

**Files:**
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/cli.py`
- Modify: `/Users/woody/ai/stockanalysis/tests/test_ingest_cli.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_sec_companyfacts.py`

**Step 1: runner failing test를 쓴다**

- canonical instrument lookup
- pipeline run lifecycle
- CLI summary

**Step 2: minimal runner를 구현한다**

- fixture 또는 live companyfacts payload load
- exact-match instrument lookup
- pipeline run 생성과 upsert 실행

### Task 4: integration verify와 운영 문서 추가

**Files:**
- Create: `/Users/woody/ai/stockanalysis/tests/fixtures/sec_companyfacts_CIK0000320193.json`
- Create: `/Users/woody/ai/stockanalysis/scripts/verify_sec_companyfacts_ingest.sh`
- Create: `/Users/woody/ai/stockanalysis/docs/sec-companyfacts-ingest.md`
- Modify: `/Users/woody/ai/stockanalysis/README.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/verification-plan.md`

**Step 1: docker verify를 추가한다**

- filings metadata ingest
- canonical Apple issuer/instrument insert
- fixture 기반 companyfacts upsert
- period/metric row count 확인

**Step 2: 운영 문서를 마무리한다**

- supported metric map
- current limits
- next step
