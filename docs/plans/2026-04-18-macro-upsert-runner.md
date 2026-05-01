# Macro Upsert Runner Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** `macro-sync` 결과를 canonical Postgres에 실제 적용하고 `ops.pipeline_run`에 실행 이력을 남기는 첫 upsert 경로를 만든다.

**Architecture:** 기존 `macro-sync` 정규화 경로는 유지하고, 그 위에 `psql` 명령 실행기와 `macro-upsert` runner를 추가한다. runner는 pipeline run 생성, SQL upsert 실행, 성공/실패 상태 갱신만 책임지고 scheduler나 batch orchestration은 뒤로 미룬다.

**Tech Stack:** Python 3.11, stdlib `subprocess`, Postgres `psql`, existing unittest, docker-based verification scripts

---

### Task 1: Task 문서와 구현 경계 고정

**Files:**
- Create: `docs/tasks/macro-upsert-runner/contract.md`
- Create: `docs/tasks/macro-upsert-runner/plan.md`
- Create: `docs/tasks/macro-upsert-runner/handoff.md`
- Create: `docs/tasks/macro-upsert-runner/review.md`
- Modify: `docs/tasks/macro-ingest/handoff.md`

**Step 1: 작업 계약과 범위를 문서화한다**

- `macro-ingest` 다음 단계임을 명시한다.
- direct execute만 포함하고 batch orchestration은 제외한다.

**Step 2: 검증 계획을 적는다**

- `bash scripts/verify_macro_upsert_runner.sh`
- `awh verify --task macro-upsert-runner`

### Task 2: `psql` 실행기와 runner 구현

**Files:**
- Create: `src/stockanalysis/ingest/psql.py`
- Create: `src/stockanalysis/ingest/macro/upsert.py`
- Modify: `src/stockanalysis/ingest/config.py`
- Modify: `src/stockanalysis/ingest/macro/sql.py`
- Modify: `src/stockanalysis/ingest/cli.py`

**Step 1: 설정에 `STOCKANALYSIS_PSQL_COMMAND`를 추가한다**

**Step 2: `psql` 명령 실행기 최소 구현을 넣는다**

- scalar query
- non-query execution
- stderr 기반 에러 표면화

**Step 3: `macro-upsert` runner를 구현한다**

- pipeline run 생성
- macro SQL 실행
- 성공/실패 상태 갱신

**Step 4: CLI 명령을 연결한다**

- `macro-upsert`

### Task 3: 테스트와 검증 스크립트 추가

**Files:**
- Create: `tests/test_macro_upsert.py`
- Modify: `tests/test_ingest_cli.py`
- Create: `scripts/verify_macro_upsert_runner.sh`

**Step 1: unit test를 추가한다**

- 성공 경로
- 실패 시 `failed` 상태 기록
- CLI summary 출력

**Step 2: docker 기반 integration verify를 추가한다**

- migrations + seeds
- fixture upsert
- row count / status 확인

### Task 4: 문서와 handoff 정리

**Files:**
- Create: `docs/macro-upsert-runner.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/macro-upsert-runner/*.md`

**Step 1: 운영 문서를 갱신한다**

- env var contract
- CLI usage
- current limits

**Step 2: 검증 결과를 handoff/review에 적는다**

- 실제 실행한 명령과 관찰 결과를 남긴다.
