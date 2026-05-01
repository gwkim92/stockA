# Strategy Universe Slicing Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** canonical market universe와 price bars를 이용해 중장기 전략용 universe snapshot을 `signal.strategy_universe_*` tables에 저장하는 `strategy-universe-slice` 경로를 만든다.

**Architecture:** 새로운 signal-layer tables를 추가해 canonical universe와 recommendation 사이에 전략 universe snapshot을 둔다. runner는 active instruments, exchange filter, price data availability, minimum observation count, minimum adjusted close 조건으로 후보를 자르고 snapshot batch/member rows를 upsert한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: schema와 task 문서 고정

**Files:**
- Create: `db/migrations/0004_strategy_universe.sql`
- Create: `docs/tasks/strategy-universe-slicing/contract.md`
- Create: `docs/tasks/strategy-universe-slicing/plan.md`
- Create: `docs/tasks/strategy-universe-slicing/handoff.md`
- Create: `docs/tasks/strategy-universe-slicing/review.md`
- Modify: `docs/tasks/market-price-universe-backfill/handoff.md`

**Step 1: Write the schema migration**

- Add `signal.strategy_universe_batch`
- Add `signal.strategy_universe_member`
- Add indexes for batch identity and member lookup

**Step 2: Record the task contract**

- Scope includes fixture-based strategy slicing
- Scope excludes cycle score, theme membership, AI ranking, live scheduling

### Task 2: runner와 CLI 구현

**Files:**
- Create: `src/stockanalysis/signal/__init__.py`
- Create: `src/stockanalysis/signal/universe.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Create: `tests/test_strategy_universe.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Write unit tests**

- candidate lookup SQL includes price availability filters
- runner creates pipeline run, upserts batch/member rows, marks success
- runner marks failure when upsert errors
- CLI prints JSON summary

**Step 2: Implement minimal code**

- Load candidate rows as JSON
- Create `ops.pipeline_run`
- Upsert universe batch and replace members
- Return summary with counts and preview

### Task 3: verification, docs, AI role map

**Files:**
- Create: `scripts/verify_strategy_universe_slicing.sh`
- Create: `docs/strategy-universe-slicing.md`
- Create: `docs/ai-role-map.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`

**Step 1: Add Docker integration verify**

- Run migrations/seeds
- Run market universe bootstrap
- Run market price universe backfill
- Run strategy universe slice
- Assert batch/member rows and pipeline status

**Step 2: Document operational usage**

- CLI usage
- selection rules
- current limitations

**Step 3: Document where AI fits**

- LLM as event/thesis/review/report intelligence
- deterministic scoring and portfolio constraints remain separate from LLM generation
