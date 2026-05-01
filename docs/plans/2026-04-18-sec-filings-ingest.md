# SEC Filings Ingest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** SEC submissions API의 filing 메타데이터를 canonical Postgres `ingest.source_document`에 적재하는 첫 공시 ingest 경로를 만든다.

**Architecture:** SEC source adapter는 그대로 유지하고, 그 위에 submissions payload 정규화, SQL upsert renderer, `sec-filings-upsert` runner를 추가한다. 현재 단계는 문서 메타데이터까지만 다루고, filing body/raw artifact나 issuer mapping은 뒤로 미룬다.

**Tech Stack:** Python 3.11, Postgres `psql`, existing ingest CLI, unittest, docker-based verification scripts

---

### Task 1: SEC filings ingest 범위와 task 문서 고정

**Files:**
- Create: `docs/tasks/sec-filings-ingest/contract.md`
- Create: `docs/tasks/sec-filings-ingest/plan.md`
- Create: `docs/tasks/sec-filings-ingest/handoff.md`
- Create: `docs/tasks/sec-filings-ingest/review.md`
- Modify: `docs/tasks/macro-run-history-report/handoff.md`

**Step 1: 범위를 source_document ingest로 고정한다**

**Step 2: 검증 경로를 적는다**

- `bash scripts/verify_sec_filings_ingest.sh`
- `awh verify --task sec-filings-ingest`

### Task 2: SEC filings 정규화와 upsert 구현

**Files:**
- Create: `src/stockanalysis/ingest/sec/models.py`
- Create: `src/stockanalysis/ingest/sec/submissions.py`
- Create: `src/stockanalysis/ingest/sec/sql.py`
- Create: `src/stockanalysis/ingest/sec/upsert.py`
- Modify: `src/stockanalysis/ingest/cli.py`

**Step 1: submissions payload를 filing record로 정규화한다**

**Step 2: source_document upsert SQL을 만든다**

**Step 3: `sec-filings-upsert` runner와 CLI를 연결한다**

### Task 3: Fixture, 테스트, integration verify 추가

**Files:**
- Create: `tests/fixtures/sec_submissions_CIK0000320193.json`
- Create: `tests/test_sec_filings.py`
- Modify: `tests/test_ingest_cli.py`
- Create: `scripts/verify_sec_filings_ingest.sh`

**Step 1: Apple submissions fixture를 추가한다**

**Step 2: 정규화/SQL/upsert unit test를 쓴다**

**Step 3: docker 기반 source_document upsert 검증을 추가한다**

### Task 4: 운영 문서와 handoff 정리

**Files:**
- Create: `docs/sec-filings-ingest.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/sec-filings-ingest/*.md`

**Step 1: 운영 문서를 갱신한다**

- CLI usage
- current mapping
- current limits

**Step 2: 검증 결과를 기록한다**
