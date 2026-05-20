# Broker Safety Boundary And Stock Link Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the missing safety prerequisites for future paper/live trading and fix the stock list so only each stock identifier is clickable.

**Architecture:** This is a safety-boundary slice, not a broker integration. The system gets a `trading` schema, a deterministic Python order safety evaluator, and tests proving orders stay blocked unless broker boundary, account permission, order limits, kill switch, paper validation, and human approval all pass. The frontend stock list stops wrapping entire rows in links.

**Tech Stack:** Python dataclasses/Decimal, Postgres SQL migration, unittest, Next.js App Router, CSS.

---

### Task 1: Task Contract

**Files:**
- Create: `docs/tasks/broker-safety-boundary-and-stock-link-fix/contract.md`
- Create: `docs/tasks/broker-safety-boundary-and-stock-link-fix/handoff.md`

**Steps:**
- Record that this slice implements broker safety boundary prerequisites only.
- Record that no real broker adapter, credentials, account login, or order submission is implemented.
- Record stock row click fix as part of the same operator usability task.

### Task 2: Trading Safety Schema

**Files:**
- Create: `db/migrations/0013_trading_safety_boundary.sql`

**Steps:**
- Add `trading` schema.
- Add broker boundary, account permission, order limit policy, kill switch, paper validation run, and order intent audit tables.
- Add safe defaults: global kill switch engaged by default.
- Add check constraints and indexes.
- Do not store secrets. Store only `secret_ref` or opaque account refs.

### Task 3: Deterministic Safety Evaluator

**Files:**
- Create: `src/stockanalysis/trading/__init__.py`
- Create: `src/stockanalysis/trading/safety.py`
- Test: `tests/test_trading_safety.py`

**Steps:**
- Model order intent, broker boundary, account permission, order limits, kill switch, paper validation, and decision.
- Block by default.
- Require human approval before paper/live order approval.
- Require passed paper validation before live order approval.
- Return audit payload without secrets.

### Task 4: Stock Row Link Fix

**Files:**
- Modify: `apps/web/src/app/stocks/page.tsx`
- Modify: `apps/web/src/app/globals.css`

**Steps:**
- Replace row-level `Link` with a normal row container.
- Make only the stock symbol/name cell a `Link`.
- Preserve table layout and keyboard focus style.

### Task 5: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_safety`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- Playwright snapshot for `http://127.0.0.1:3001/stocks`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task broker-safety-boundary-and-stock-link-fix`
- `git diff --check`
