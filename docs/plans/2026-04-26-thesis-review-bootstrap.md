# Thesis Review Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** active investment thesis가 현재 linked recommendation과 cycle evidence 기준으로 여전히 유효한지 deterministic review row로 저장한다.

**Architecture:** 이번 bootstrap은 LLM review prose를 만들지 않는다. `signal.investment_thesis`와 linked active `signal.recommendation`을 읽고, current cycle/feature evidence를 붙여 `signal.thesis_review`에 review action, health score, summary, next review date를 upsert한다. `signal.thesis_review`는 문서에만 있던 설계를 실제 migration으로 추가한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: schema와 task boundary 고정

**Files:**
- Create: `docs/plans/2026-04-26-thesis-review-bootstrap.md`
- Create: `docs/tasks/thesis-review-bootstrap/contract.md`
- Create: `docs/tasks/thesis-review-bootstrap/plan.md`
- Create: `docs/tasks/thesis-review-bootstrap/handoff.md`
- Create: `docs/tasks/thesis-review-bootstrap/review.md`
- Create: `db/migrations/0007_thesis_review.sql`

**Step 1: Fix scope**

- Include active thesis linked to active recommendation rows in one recommendation batch identity
- Include current cycle snapshot and market feature evidence when available
- Create or update `signal.thesis_review`
- Exclude LLM prose, portfolio execution, thesis status mutation, and trade automation

### Task 2: runner와 CLI 구현

**Files:**
- Create: `src/stockanalysis/signal/thesis_review.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Create: `tests/test_thesis_review_bootstrap.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add tests**

- candidate lookup SQL joins recommendation batch, recommendation, investment thesis, instrument, cycle state, and feature values
- review row renderer produces deterministic action, health score, summary, next review date
- upsert SQL writes `signal.thesis_review` with conflict update
- runner creates pipeline run and marks success/failure
- CLI prints summary

**Step 2: Implement**

- Look up thesis review candidates for one batch identity
- Compute deterministic review rows
- Upsert review rows by `(thesis_id, review_date, review_source)`
- Return summary with review count and action counts

### Task 3: verification과 docs

**Files:**
- Create: `scripts/verify_thesis_review_bootstrap.sh`
- Create: `docs/thesis-review-bootstrap.md`
- Modify: `README.md`
- Modify: `docs/db-schema-design.md`
- Modify: `docs/thesis-bootstrap.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/thesis-review-bootstrap/handoff.md`
- Modify: `docs/tasks/thesis-review-bootstrap/review.md`

**Step 1: Docker verify**

- Run full chain through `thesis-bootstrap`
- Run `thesis-review-bootstrap`
- Assert thesis review row, action `watch`, health score `0.3610`, next review date, latest run status

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_thesis_review_bootstrap.sh
bash scripts/verify_thesis_review_bootstrap.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task thesis-review-bootstrap
if rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S; then exit 1; fi
```
