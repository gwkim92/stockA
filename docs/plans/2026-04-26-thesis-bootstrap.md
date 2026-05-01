# Thesis Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** deterministic recommendation rows에 active investment thesis를 생성 또는 갱신해 `signal.investment_thesis`와 `signal.recommendation.thesis_id`를 연결한다.

**Architecture:** 이번 bootstrap은 AI가 thesis를 작성하지 않는다. recommendation batch, direct theme membership, cycle state, instrument feature snapshot을 읽어 templated thesis를 만들고, 같은 instrument/node/thesis_type의 active thesis가 있으면 갱신하고 없으면 생성한다. thesis factor/review table과 LLM explanation은 후속 task로 분리한다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: task boundary와 thesis contract 고정

**Files:**
- Create: `docs/plans/2026-04-26-thesis-bootstrap.md`
- Create: `docs/tasks/thesis-bootstrap/contract.md`
- Create: `docs/tasks/thesis-bootstrap/plan.md`
- Create: `docs/tasks/thesis-bootstrap/handoff.md`
- Create: `docs/tasks/thesis-bootstrap/review.md`

**Step 1: Fix scope**

- Include active recommendation rows from one recommendation batch identity
- Include direct `derived_theme` membership and cycle snapshot evidence
- Create or update active `signal.investment_thesis`
- Link `signal.recommendation.thesis_id`
- Exclude AI-generated prose, thesis factors, thesis review, and portfolio action

### Task 2: runner와 CLI 구현

**Files:**
- Create: `src/stockanalysis/signal/thesis.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Create: `tests/test_thesis_bootstrap.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add tests**

- candidate lookup SQL joins recommendation batch, recommendation, instrument, membership, cycle state, and feature values
- thesis row renderer produces deterministic title, summary, invalidation conditions
- upsert SQL updates existing active thesis or inserts a new one and links recommendation
- runner creates pipeline run and marks success/failure
- CLI prints summary

**Step 2: Implement**

- Look up recommendation thesis candidates for one batch identity
- Render active thesis rows with deterministic text and expected holding period
- Upsert active thesis rows and link recommendation rows
- Return summary with linked thesis count

### Task 3: verification과 docs

**Files:**
- Create: `scripts/verify_thesis_bootstrap.sh`
- Create: `docs/thesis-bootstrap.md`
- Modify: `README.md`
- Modify: `docs/db-schema-design.md`
- Modify: `docs/recommendation-bootstrap.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/thesis-bootstrap/handoff.md`
- Modify: `docs/tasks/thesis-bootstrap/review.md`

**Step 1: Docker verify**

- Run full chain through `recommendation-bootstrap`
- Run `thesis-bootstrap`
- Assert investment thesis row, linked recommendation, thesis title/status, and latest run status

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_thesis_bootstrap.sh
bash scripts/verify_thesis_bootstrap.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task thesis-bootstrap
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
