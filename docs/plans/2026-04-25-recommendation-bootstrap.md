# Recommendation Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** selected strategy universe, market features, direct theme membership, and cycle state snapshots를 이용해 deterministic recommendation batch와 recommendation rows를 `signal.recommendation_batch`, `signal.recommendation`에 저장한다.

**Architecture:** 이번 bootstrap은 AI ranking이나 thesis 생성을 하지 않는다. `strategy_universe_member`를 investable boundary로 쓰고, direct `derived_theme` membership과 `cycle_state_snapshot`, instrument feature values를 조합해 instrument-node candidate를 만든 뒤 instrument별 최고 점수 candidate만 저장한다. 기존 `recommendation_score_component` table은 아직 migration에 없으므로 component detail은 batch notes와 deterministic code/docs에 고정한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: task boundary와 scoring contract 고정

**Files:**
- Create: `docs/plans/2026-04-25-recommendation-bootstrap.md`
- Create: `docs/tasks/recommendation-bootstrap/contract.md`
- Create: `docs/tasks/recommendation-bootstrap/plan.md`
- Create: `docs/tasks/recommendation-bootstrap/handoff.md`
- Create: `docs/tasks/recommendation-bootstrap/review.md`

**Step 1: Fix scope**

- Include selected strategy universe only
- Include direct `derived_theme` memberships under `internal_theme`
- Include existing market feature snapshot and cycle state snapshot
- Exclude investment thesis creation, AI ranking, portfolio sizing, and score component table

### Task 2: runner와 CLI 구현

**Files:**
- Create: `src/stockanalysis/signal/recommendation.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Create: `tests/test_recommendation_bootstrap.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add tests**

- candidate lookup SQL joins strategy universe, theme membership, cycle state, and feature values
- score calculator maps a fixture AAPL candidate to expected total score and `watch` bucket
- upsert SQL rewrites one recommendation batch and ranked rows
- runner creates pipeline run and marks success/failure
- CLI prints summary

**Step 2: Implement**

- Look up instrument-node candidates for one strategy universe identity
- Compute momentum, short-term, rank, and cycle component scores
- Select the highest-scoring candidate per instrument
- Upsert `signal.recommendation_batch`
- Delete and rewrite `signal.recommendation` rows for the batch

### Task 3: verification과 docs

**Files:**
- Create: `scripts/verify_recommendation_bootstrap.sh`
- Create: `docs/recommendation-bootstrap.md`
- Modify: `README.md`
- Modify: `docs/cycle-state-snapshot.md`
- Modify: `docs/db-schema-design.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/recommendation-bootstrap/handoff.md`
- Modify: `docs/tasks/recommendation-bootstrap/review.md`

**Step 1: Docker verify**

- Run market universe bootstrap, price backfill, strategy universe slice
- Run market feature snapshot
- Run SEC filing ingest/raw/event extract
- Run classification and instrument impact bootstrap
- Run instrument theme enrichment
- Run cycle state snapshot
- Run recommendation bootstrap
- Assert recommendation batch, recommendation row, AAPL rank/bucket/action, and latest run status

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_recommendation_bootstrap.sh
bash scripts/verify_recommendation_bootstrap.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task recommendation-bootstrap
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
