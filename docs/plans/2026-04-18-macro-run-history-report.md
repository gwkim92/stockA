# Macro Run History Report Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 최근 macro upsert 실행 이력을 canonical Postgres에서 조회하는 report/audit 경로를 만든다.

**Architecture:** 기존 `ops.pipeline_run`과 `macro.observation.source_run_id`를 이용해 최근 run 요약을 SQL로 계산하고, CLI가 JSON report로 노출한다. report는 read-only 경로이며 single-series와 batch 적재기 모두가 남긴 run 이력을 통합해서 보여준다.

**Tech Stack:** Python 3.11, Postgres `psql`, existing ingest CLI, unittest, docker-based verification scripts

---

### Task 1: report 범위와 task 문서 고정

**Files:**
- Create: `docs/tasks/macro-run-history-report/contract.md`
- Create: `docs/tasks/macro-run-history-report/plan.md`
- Create: `docs/tasks/macro-run-history-report/handoff.md`
- Create: `docs/tasks/macro-run-history-report/review.md`
- Modify: `docs/tasks/macro-batch-upsert/handoff.md`

**Step 1: 조회 범위와 필드를 문서화한다**

- recent run list
- status counts
- per-run observation count

**Step 2: 검증 경로를 적는다**

- `bash scripts/verify_macro_run_history_report.sh`
- `awh verify --task macro-run-history-report`

### Task 2: report query와 CLI 구현

**Files:**
- Create: `src/stockanalysis/ingest/macro/report.py`
- Modify: `src/stockanalysis/ingest/cli.py`

**Step 1: recent run JSON report query를 구현한다**

**Step 2: `macro-run-history` CLI를 연결한다**

### Task 3: 테스트와 integration verify 추가

**Files:**
- Create: `tests/test_macro_report.py`
- Modify: `tests/test_ingest_cli.py`
- Create: `scripts/verify_macro_run_history_report.sh`

**Step 1: report loader unit test를 추가한다**

**Step 2: batch upsert 후 report query를 검증한다**

### Task 4: 문서와 handoff 정리

**Files:**
- Create: `docs/macro-run-history-report.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/macro-run-history-report/*.md`

**Step 1: 운영 문서를 갱신한다**

- CLI usage
- report shape
- current limits

**Step 2: 검증 결과를 기록한다**
