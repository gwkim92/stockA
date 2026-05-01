# Instrument Theme Enrichment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** strategy universe members와 existing event impacts를 이용해 bootstrap instrument-theme memberships를 `ref.instrument_classification_membership`에 저장하는 `instrument-theme-enrichment` 경로를 만든다.

**Architecture:** `strategy-universe-slice`가 고정한 investable universe와 `event.event_instrument_impact`, `event.event_classification_impact`를 조인해 theme/subtheme memberships를 파생한다. 이번 단계는 internal theme taxonomy에 한정하고, 기존 derived theme memberships를 selected universe 범위에서 교체 저장해 deterministic snapshot-like enrichment를 만든다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: task boundary와 docs 고정

**Files:**
- Create: `docs/plans/2026-04-23-instrument-theme-enrichment.md`
- Create: `docs/tasks/instrument-theme-enrichment/contract.md`
- Create: `docs/tasks/instrument-theme-enrichment/plan.md`
- Create: `docs/tasks/instrument-theme-enrichment/handoff.md`
- Create: `docs/tasks/instrument-theme-enrichment/review.md`

**Step 1: Fix scope**

- Include selected strategy universe instruments only
- Include internal theme taxonomy only
- Exclude fuzzy matching, external taxonomy ingestion, parent propagation beyond direct event-linked node

### Task 2: runner와 CLI 구현

**Files:**
- Create: `src/stockanalysis/signal/theme_enrichment.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Create: `tests/test_instrument_theme_enrichment.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add tests**

- candidate lookup SQL joins strategy universe and event impacts
- candidate load returns expected AAPL -> ANNUAL_REPORTING row
- replace SQL rewrites selected universe memberships
- runner creates pipeline run and marks success/failure
- CLI prints summary

**Step 2: Implement**

- Look up selected strategy universe batch members
- Join event instrument impacts and classification impacts through internal theme nodes
- Aggregate supporting_event_count, confidence, first/latest event date
- Replace `derived_theme` memberships for selected universe instruments

### Task 3: verification과 docs

**Files:**
- Create: `scripts/verify_instrument_theme_enrichment.sh`
- Create: `docs/instrument-theme-enrichment.md`
- Modify: `README.md`
- Modify: `docs/db-schema-design.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/market-feature-snapshot.md`
- Modify: `docs/tasks/instrument-theme-enrichment/handoff.md`
- Modify: `docs/tasks/instrument-theme-enrichment/review.md`

**Step 1: Docker verify**

- Run market universe bootstrap, price backfill, strategy universe slice
- Run SEC filing ingest/raw/event extract
- Run classification and instrument impact bootstrap
- Run instrument theme enrichment
- Assert `ref.instrument_classification_membership` rows and latest run status

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_instrument_theme_enrichment.sh
bash scripts/verify_instrument_theme_enrichment.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task instrument-theme-enrichment
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
