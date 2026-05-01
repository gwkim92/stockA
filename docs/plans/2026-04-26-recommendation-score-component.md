# Recommendation Score Component Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** recommendation total score를 구성하는 component score와 weight를 canonical DB에 저장해 추천 판단을 감사 가능하게 만든다.

**Architecture:** 기존 `recommendation-bootstrap` scoring logic은 바꾸지 않는다. 이미 계산 중인 component scores를 `signal.recommendation_score_component`에 recommendation child rows로 저장하고, recommendation 재생성 시 cascade/delete 후 같은 batch 안에서 다시 insert한다. 이번 작업은 deterministic score audit layer이며 AI ranking이나 thesis/review logic은 건드리지 않는다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: schema와 task boundary 고정

**Files:**
- Create: `docs/plans/2026-04-26-recommendation-score-component.md`
- Create: `docs/tasks/recommendation-score-component/contract.md`
- Create: `docs/tasks/recommendation-score-component/plan.md`
- Create: `docs/tasks/recommendation-score-component/handoff.md`
- Create: `docs/tasks/recommendation-score-component/review.md`
- Create: `db/migrations/0008_recommendation_score_component.sql`

**Step 1: Fix scope**

- Include score component persistence for rows created by `recommendation-bootstrap`
- Include component score, component weight, and deterministic explanation
- Exclude score formula changes, AI ranking, thesis/review changes, and portfolio action

### Task 2: recommendation persistence 구현

**Files:**
- Modify: `src/stockanalysis/signal/recommendation.py`
- Modify: `tests/test_recommendation_bootstrap.py`

**Step 1: Add tests**

- `RecommendationRow` still calculates component scores
- upsert SQL inserts `signal.recommendation_score_component`
- SQL stores component weight and explanation
- runner summary includes component row count

**Step 2: Implement**

- Add component weight lookup helper
- Render component value tuples from `RecommendationRow.component_scores`
- Insert recommendation rows with `returning recommendation_id, instrument_id`
- Insert score component rows joined by instrument id
- Return expected component row count in summary

### Task 3: verification과 docs

**Files:**
- Create: `scripts/verify_recommendation_score_component.sh`
- Create: `docs/recommendation-score-component.md`
- Modify: `README.md`
- Modify: `docs/db-schema-design.md`
- Modify: `docs/recommendation-bootstrap.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/recommendation-score-component/handoff.md`
- Modify: `docs/tasks/recommendation-score-component/review.md`

**Step 1: Docker verify**

- Run full chain through `recommendation-bootstrap`
- Assert recommendation row and four score component rows
- Assert AAPL component scores and latest pipeline run status

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_recommendation_score_component.sh
bash scripts/verify_recommendation_score_component.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task recommendation-score-component
if rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S; then exit 1; fi
```
