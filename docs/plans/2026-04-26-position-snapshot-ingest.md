# Position Snapshot Ingest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** broker/live 연동 전 단계로 표준 CSV position snapshot을 canonical `portfolio.position_snapshot`에 업서트한다.

**Architecture:** 기존 `portfolio.portfolio`와 `portfolio.position_snapshot` schema를 유지한다. CSV loader가 position rows를 정규화하고, upsert runner가 portfolio header를 생성/갱신한 뒤 symbol을 canonical instrument에 매핑해 snapshot rows를 저장한다.

**Tech Stack:** Python 3 stdlib `csv`, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: 작업 경계와 문서 scaffold

**Files:**
- Create: `docs/plans/2026-04-26-position-snapshot-ingest.md`
- Create: `docs/tasks/position-snapshot-ingest/contract.md`
- Create: `docs/tasks/position-snapshot-ingest/plan.md`
- Create: `docs/tasks/position-snapshot-ingest/handoff.md`
- Create: `docs/tasks/position-snapshot-ingest/review.md`

**Step 1: Fix scope**

- Include CSV fixture ingestion into `portfolio.position_snapshot`.
- Include portfolio upsert, symbol-to-instrument mapping, optional active thesis link.
- Exclude broker API, real account sync, trade/order generation, portfolio optimizer.

### Task 2: CSV loader와 upsert runner 구현

**Files:**
- Create: `src/stockanalysis/ingest/portfolio/__init__.py`
- Create: `src/stockanalysis/ingest/portfolio/position.py`
- Create: `tests/fixtures/portfolio_positions_long_term_paper.csv`
- Create: `tests/test_position_snapshot_ingest.py`
- Modify: `src/stockanalysis/ingest/cli.py`
- Modify: `tests/test_ingest_cli.py`

**Step 1: Add tests**

- CSV loader parses AAPL row and Decimal fields.
- SQL renderer upserts `portfolio.portfolio` and `portfolio.position_snapshot`.
- runner records `ops.pipeline_run` and returns position counts.
- CLI command prints JSON summary.

**Step 2: Implement**

- Define `PositionSnapshotRecord` and `PositionSnapshotSyncResult`.
- Parse required CSV columns: `symbol`, `quantity`, `market_price`, `market_value`.
- Parse optional CSV columns: `cost_basis`, `weight`, `unrealized_pnl`, `linked_thesis_id`.
- Render SQL with portfolio upsert and source rows.
- Resolve canonical instrument by `ref.instrument.primary_symbol`.
- Link active thesis when CSV does not provide `linked_thesis_id`.
- Add `portfolio-position-snapshot-upsert` CLI.

### Task 3: verification과 docs

**Files:**
- Create: `scripts/verify_position_snapshot_ingest.sh`
- Create: `docs/position-snapshot-ingest.md`
- Modify: `scripts/verify_portfolio_review_bootstrap.sh`
- Modify: `README.md`
- Modify: `docs/db-schema-design.md`
- Modify: `docs/portfolio-review-bootstrap.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/position-snapshot-ingest/handoff.md`
- Modify: `docs/tasks/position-snapshot-ingest/review.md`

**Step 1: Docker verify**

- Run full chain through `thesis-review-bootstrap`.
- Run `portfolio-position-snapshot-upsert` with CSV fixture.
- Assert portfolio 1건, AAPL position snapshot 1건, linked active thesis 1건, latest `portfolio_position_snapshot_upsert` run status `succeeded`.
- Run `portfolio-review-bootstrap` using the ingested snapshot and assert AAPL action `monitor`.

**Step 2: Final verification**

Run:

```bash
python3 -m compileall src tests
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n scripts/verify_position_snapshot_ingest.sh
bash -n scripts/verify_portfolio_review_bootstrap.sh
bash scripts/verify_position_snapshot_ingest.sh
bash scripts/verify_portfolio_review_bootstrap.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task position-snapshot-ingest
if rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S; then exit 1; fi
```
