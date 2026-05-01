# Macro Batch Upsert Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 여러 기본 거시 series를 한 번에 canonical Postgres에 적재하는 `macro-batch-upsert` 경로를 만든다.

**Architecture:** 기존 `macro-upsert` runner를 재사용하고, batch wrapper가 default series 목록과 fixture directory resolution만 추가한다. batch는 series별 개별 `pipeline_run`을 유지하고 전체 summary를 별도로 반환한다.

**Tech Stack:** Python 3.11, stdlib, existing `psql` runner, unittest, docker-based verification scripts

---

### Task 1: Batch 범위와 task 문서 고정

**Files:**
- Create: `docs/tasks/macro-batch-upsert/contract.md`
- Create: `docs/tasks/macro-batch-upsert/plan.md`
- Create: `docs/tasks/macro-batch-upsert/handoff.md`
- Create: `docs/tasks/macro-batch-upsert/review.md`
- Modify: `docs/tasks/macro-upsert-runner/handoff.md`

**Step 1: batch 경계를 문서화한다**

- default series only
- fixture directory mode
- series별 pipeline run 유지

**Step 2: 검증 경로를 적는다**

- `bash scripts/verify_macro_batch_upsert.sh`
- `awh verify --task macro-batch-upsert`

### Task 2: Batch runner와 CLI 구현

**Files:**
- Modify: `src/stockanalysis/ingest/macro/upsert.py`
- Modify: `src/stockanalysis/ingest/cli.py`

**Step 1: default spec resolver를 추가한다**

**Step 2: fixture directory resolver를 추가한다**

**Step 3: batch summary를 반환하는 runner를 구현한다**

**Step 4: `macro-batch-upsert` CLI를 연결한다**

### Task 3: Fixture, 테스트, verification 추가

**Files:**
- Create: `tests/fixtures/fred_series_FEDFUNDS.json`
- Create: `tests/fixtures/fred_observations_FEDFUNDS.json`
- Modify: `tests/test_ingest_cli.py`
- Modify: `tests/test_macro_upsert.py`
- Create: `scripts/verify_macro_batch_upsert.sh`

**Step 1: 두 번째 fixture series를 추가한다**

**Step 2: batch success/failure unit test를 쓴다**

**Step 3: docker 기반 batch integration verify를 추가한다**

### Task 4: 문서와 handoff 마무리

**Files:**
- Create: `docs/macro-batch-upsert.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/macro-batch-upsert/*.md`

**Step 1: 운영 문서를 갱신한다**

- CLI usage
- batch summary shape
- current limits

**Step 2: 검증 결과를 기록한다**
