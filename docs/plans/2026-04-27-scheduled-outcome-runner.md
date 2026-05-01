# Scheduled Outcome Runner Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 추천 batch별로 due horizon을 자동 탐색해 performance outcome을 생성하는 scheduled runner를 추가한다.

**Architecture:** `signal.recommendation_batch`와 `performance.recommendation_outcome`을 비교해 아직 outcome이 없는 `(batch, horizon_day)` 후보를 찾는다. 실행은 기존 `run_performance_outcome_bootstrap`을 재사용하고, schedule parent run은 `ops.pipeline_run`에 별도 기록한다.

**Tech Stack:** Python stdlib, argparse CLI, Postgres SQL, existing psql executor, Docker verification script.

---

### Task 1: Task Harness

**Files:**
- Create: `docs/tasks/scheduled-outcome-runner/contract.md`
- Create: `docs/tasks/scheduled-outcome-runner/plan.md`
- Create: `docs/tasks/scheduled-outcome-runner/handoff.md`
- Create: `docs/tasks/scheduled-outcome-runner/review.md`

**Steps:**
- scheduled outcome runner의 scope, mutable surface, verification commands를 문서화한다.
- `handoff.md`에는 현재 상태와 exact next step을 남긴다.

### Task 2: Schedule Candidate Lookup

**Files:**
- Modify: `src/stockanalysis/performance/outcome.py`
- Test: `tests/test_performance_outcome_bootstrap.py`

**Steps:**
- `PerformanceOutcomeScheduleCandidate` dataclass를 추가한다.
- `resolve_performance_schedule_horizon_days`를 추가해 default `(30, 90, 180, 365)`와 dedupe/sort/positive validation을 처리한다.
- `render_performance_outcome_schedule_candidate_lookup_sql`을 추가한다.
- `load_performance_outcome_schedule_candidates`를 추가한다.
- unit test로 SQL shape, parsing, default horizon, invalid horizon을 검증한다.

### Task 3: Schedule Runner

**Files:**
- Modify: `src/stockanalysis/performance/outcome.py`
- Test: `tests/test_performance_outcome_bootstrap.py`

**Steps:**
- `run_performance_outcome_schedule_bootstrap`를 추가한다.
- parent `performance_outcome_schedule_bootstrap` pipeline run을 생성한다.
- 후보별로 기존 `run_performance_outcome_bootstrap`을 호출한다.
- candidate 실패는 summary에 기록하고 다음 candidate로 계속 진행한다.
- 실패가 하나라도 있으면 parent run은 `failed`, 전부 성공하면 `succeeded`로 표시한다.

### Task 4: CLI

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Test: `tests/test_ingest_cli.py`

**Steps:**
- CLI `performance-outcome-schedule-bootstrap`를 추가한다.
- args: `--due-on-date`, repeatable `--horizon-day`, optional filters `--market-code`, `--strategy-name`, `--horizon-type`, `--universe-version`, `--limit`, `--outcome-version`.
- handler는 failed candidate가 있으면 exit code 1을 반환한다.

### Task 5: Docker Verification

**Files:**
- Create: `scripts/verify_scheduled_outcome_runner.sh`

**Steps:**
- 기존 performance outcome verify pipeline을 재사용한다.
- direct batch outcome CLI 대신 schedule CLI를 실행한다.
- 2024-11-01 batch에 대해 horizon 3일과 31일 outcome 2건을 확인한다.
- parent schedule pipeline run status와 child outcome rows를 확인한다.

### Task 6: Documentation

**Files:**
- Create: `docs/scheduled-outcome-runner.md`
- Modify: `README.md`
- Modify: `docs/performance-outcome-bootstrap.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/scheduled-outcome-runner/handoff.md`
- Modify: `docs/tasks/scheduled-outcome-runner/review.md`

**Steps:**
- schedule runner의 역할, CLI, due candidate 기준, boundaries를 문서화한다.
- verification evidence를 handoff/review에 남긴다.
