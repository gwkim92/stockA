# Frontend Live Read Cycle List Implementation Plan

**Goal:** `/api/cycles?asOfDate=...` endpoint를 canonical Postgres live read DTO로 확장한다.

**Architecture:** 기존 `src/stockanalysis/frontend/live_adapter.py`의 read-only live adapter 패턴을 유지한다. cycle list는 `signal.cycle_state_snapshot`의 기준일 이하 최신 snapshot을 theme별로 선택하고, instrument membership과 feature score를 결합해 frontend contract shape로 변환한다.

**Tech Stack:** Python stdlib, Postgres JSON builders, existing `PsqlCommandExecutor`, `unittest`, agent-work-harness.

---

### Task 1: Task Harness

**Files:**
- Create: `docs/tasks/frontend-live-read-cycle-list/contract.md`
- Create: `docs/tasks/frontend-live-read-cycle-list/plan.md`
- Create: `docs/tasks/frontend-live-read-cycle-list/handoff.md`
- Create: `docs/tasks/frontend-live-read-cycle-list/review.md`

**Steps:**
- Record scope: cycle state list live read only.
- Exclude DB schema, scoring formula, benchmark/evaluation split, frontend redesign, and production API server.
- Record validation commands.

### Task 2: Live Adapter Route

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Route `/api/cycles`.
- Require `asOfDate`.
- Keep invalid or unsupported live paths rejected.

### Task 3: SQL Renderer And DTO Builder

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add cycle list SQL from `signal.cycle_state_snapshot`, `ref.classification_node`, `ref.instrument_classification_membership`, `ref.instrument`, and optional latest `signal.strategy_universe_batch`.
- Select latest snapshot per internal theme at or before `asOfDate`.
- Add previous state, instrument count, top symbols, confidence, and features.
- Normalize DTO fields with helper builders.

### Task 4: Verification And Docs

**Files:**
- Modify: `docs/frontend-api-adapter.md`
- Modify: `docs/frontend-api-contract.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `docs/tasks/frontend-live-read-cycle-list/handoff.md`
- Modify: `docs/tasks/frontend-live-read-cycle-list/review.md`

**Steps:**
- Update supported live endpoint list.
- Run `bash scripts/verify_frontend_live_read_adapter.sh`.
- Run `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter -v`.
- Run `bash scripts/verify_project_execution_roadmap.sh`.
- Run `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-live-read-cycle-list`.
- Run placeholder scan and `git diff --check`.
