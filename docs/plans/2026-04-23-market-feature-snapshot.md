# Market Feature Snapshot Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** strategy universe members에 대해 deterministic market features를 계산해 `signal.feature_definition`, `signal.instrument_feature_value`에 저장하는 `market-feature-snapshot` 경로를 만든다.

**Architecture:** `strategy-universe-slice`가 저장한 universe snapshot을 입력 boundary로 사용하고, `market.daily_price_bar`에서 각 instrument의 bounded price history를 읽어 bootstrap feature set을 계산한다. 결과는 feature definition metadata와 instrument feature snapshot rows로 upsert하고, 각 row는 universe batch id와 feature set version을 evidence로 남긴다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: task boundary와 schema 고정

**Files:**
- Create: `docs/plans/2026-04-23-market-feature-snapshot.md`
- Create: `docs/tasks/market-feature-snapshot/contract.md`
- Create: `docs/tasks/market-feature-snapshot/plan.md`
- Create: `docs/tasks/market-feature-snapshot/handoff.md`
- Create: `docs/tasks/market-feature-snapshot/review.md`
- Create: `db/migrations/0006_market_feature_snapshot.sql`

**Step 1: Add feature tables**

- Add `signal.feature_definition`
- Add `signal.instrument_feature_value`
- Add supporting indexes

**Step 2: Fix scope**

- Include bootstrap deterministic features only
- Exclude recommendation score, cycle state, AI ranking, classification feature values

### Task 2: runner와 CLI 구현

**Files:**
- Create: `src/stockanalysis/signal/features.py`
- Modify: `src/stockanalysis/signal/__init__.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Create: `tests/test_market_feature_snapshot.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add tests**

- universe batch lookup returns price history for selected symbols
- feature computation returns expected bootstrap metrics
- upsert SQL contains definitions and feature values
- runner creates pipeline run and marks success/failure
- CLI prints summary

**Step 2: Implement**

- Load strategy universe batch members and bounded price history
- Compute `latest_adjusted_close`, `return_1d`, `return_since_first_observation`, `realized_volatility_bootstrap`, `observation_count`
- Compute cross-sectional zscores where variance exists
- Upsert feature definitions
- Upsert instrument feature values

### Task 3: verification과 docs

**Files:**
- Create: `scripts/verify_market_feature_snapshot.sh`
- Create: `docs/market-feature-snapshot.md`
- Modify: `README.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/db-schema-design.md`
- Modify: `docs/tasks/market-feature-snapshot/handoff.md`
- Modify: `docs/tasks/market-feature-snapshot/review.md`

**Step 1: Docker integration verify**

- Run market universe bootstrap
- Run market price universe backfill
- Run strategy universe slice
- Run market feature snapshot
- Assert feature definitions and per-instrument feature rows

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_market_feature_snapshot.sh
bash scripts/verify_market_feature_snapshot.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task market-feature-snapshot
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
