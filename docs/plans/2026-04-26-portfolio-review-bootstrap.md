# Portfolio Review Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** position snapshot, recommendation, thesis review evidence를 결합해 포트폴리오 보유 검토 결과를 canonical DB에 저장한다.

**Architecture:** 기존 `portfolio.portfolio`와 `portfolio.position_snapshot`을 입력으로 사용하고, 새 `portfolio.review` header와 `portfolio.review_item` child rows를 저장한다. 판단은 deterministic rule로 시작하며, 주문 생성이나 실거래 자동화는 범위 밖으로 둔다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: schema와 작업 경계 고정

**Files:**
- Create: `docs/plans/2026-04-26-portfolio-review-bootstrap.md`
- Create: `docs/tasks/portfolio-review-bootstrap/contract.md`
- Create: `docs/tasks/portfolio-review-bootstrap/plan.md`
- Create: `docs/tasks/portfolio-review-bootstrap/handoff.md`
- Create: `docs/tasks/portfolio-review-bootstrap/review.md`
- Create: `db/migrations/0009_portfolio_review.sql`

**Step 1: Fix scope**

- Include portfolio review header and per-position review item persistence.
- Include deterministic action mapping from thesis review and current/recommended weights.
- Exclude trade execution, broker integration, live portfolio adapter, and AI action ranking.

### Task 2: portfolio review runner 구현

**Files:**
- Create: `src/stockanalysis/signal/portfolio_review.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Test: `tests/test_portfolio_review_bootstrap.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add tests**

- candidate lookup SQL joins `portfolio.position_snapshot`, `signal.recommendation`, `signal.investment_thesis`, and `signal.thesis_review`.
- deterministic rule maps AAPL watch thesis review to `monitor`.
- upsert SQL creates `portfolio.review` and `portfolio.review_item`.
- runner records `ops.pipeline_run` and returns action counts.
- CLI command prints JSON summary.

**Step 2: Implement**

- Load candidates for `portfolio_name`, `as_of_date`, recommendation batch identity, and thesis review source.
- Build one review header and one item per position.
- Upsert review header by `(portfolio_id, review_date, review_source)`.
- Replace review items under the same header to keep reruns deterministic.
- Mark pipeline run succeeded or failed.

### Task 3: verification과 docs

**Files:**
- Create: `scripts/verify_portfolio_review_bootstrap.sh`
- Create: `docs/portfolio-review-bootstrap.md`
- Modify: `README.md`
- Modify: `docs/db-schema-design.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-review-bootstrap/handoff.md`
- Modify: `docs/tasks/portfolio-review-bootstrap/review.md`

**Step 1: Docker verify**

- Run full chain through `thesis-review-bootstrap`.
- Insert a paper portfolio and AAPL position snapshot linked to the active thesis.
- Run `portfolio-review-bootstrap`.
- Assert review header 1건, review item 1건, AAPL action `monitor`, current weight `0.0500`, health score `0.3610`, and latest pipeline run status `succeeded`.

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_portfolio_review_bootstrap.sh
bash scripts/verify_portfolio_review_bootstrap.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task portfolio-review-bootstrap
if rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S; then exit 1; fi
```
