# Cycle State Snapshot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** selected strategy universe와 derived theme membership, market feature snapshot, recent event evidence를 이용해 classification node별 deterministic cycle state snapshot을 `signal.cycle_state_snapshot`에 저장한다.

**Architecture:** 이번 bootstrap은 existing canonical tables만 사용한다. `signal.instrument_feature_value`와 `ref.instrument_classification_membership`, `event.event_*_impact`를 조합해 node-level trend, breadth, event heat를 계산하고, 그 조합으로 conservative cycle state를 판정한다. parent propagation과 classification-level feature table은 이번 단계에서 제외한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: task boundary와 scoring contract 고정

**Files:**
- Create: `docs/plans/2026-04-23-cycle-state-snapshot.md`
- Create: `docs/tasks/cycle-state-snapshot/contract.md`
- Create: `docs/tasks/cycle-state-snapshot/plan.md`
- Create: `docs/tasks/cycle-state-snapshot/handoff.md`
- Create: `docs/tasks/cycle-state-snapshot/review.md`

**Step 1: Fix scope**

- Include selected strategy universe only
- Include direct `derived_theme` memberships under `internal_theme`
- Include node-level `trend_score`, `breadth_score`, `event_heat_score`, `cycle_score`, `cycle_state`
- Exclude parent propagation, classification feature table, AI scoring, recommendation logic

### Task 2: runner와 CLI 구현

**Files:**
- Create: `src/stockanalysis/signal/cycle.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Create: `tests/test_cycle_state_snapshot.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add tests**

- node-level input lookup SQL joins strategy universe, derived theme membership, instrument feature snapshot, recent event evidence
- score calculator maps feature aggregates to expected `forming`/`expanding` style states
- upsert SQL writes `signal.cycle_state_snapshot`
- runner creates pipeline run and marks success/failure
- CLI prints summary

**Step 2: Implement**

- Look up selected node-level aggregates for a single universe batch identity
- Compute `trend_score` from medium-term return zscore
- Compute `breadth_score` from positive short-term breadth
- Compute `event_heat_score` from recent event count and confidence
- Compute weighted `cycle_score` and conservative state mapping
- Replace snapshot rows for the same `as_of_date` and selected nodes

### Task 3: verification과 docs

**Files:**
- Create: `scripts/verify_cycle_state_snapshot.sh`
- Create: `docs/cycle-state-snapshot.md`
- Modify: `README.md`
- Modify: `docs/db-schema-design.md`
- Modify: `docs/instrument-theme-enrichment.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/cycle-state-snapshot/handoff.md`
- Modify: `docs/tasks/cycle-state-snapshot/review.md`

**Step 1: Docker verify**

- Run market universe bootstrap, price backfill, strategy universe slice
- Run market feature snapshot
- Run SEC filing ingest/raw/event extract
- Run classification and instrument impact bootstrap
- Run instrument theme enrichment
- Run cycle state snapshot
- Assert `signal.cycle_state_snapshot` row count, node code, cycle state, latest run status

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_cycle_state_snapshot.sh
bash scripts/verify_cycle_state_snapshot.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task cycle-state-snapshot
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
