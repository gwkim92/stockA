# Trading Readiness Cockpit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** broker boundary, account permission, order limit, kill switch, paper validation, audit log 상태를 read-only API와 화면에서 확인할 수 있게 만든다.

**Architecture:** 기존 FastAPI frontend API는 read-only boundary를 유지한다. `trading.*` 테이블은 SQL read model로만 읽고, DTO 변환은 `stockanalysis.frontend.live_adapter`에서 기존 contract 방식에 맞춰 처리한다. 화면은 Next.js server component로 `/api/trading/readiness`를 읽고, 어떤 gate가 통과/차단/누락인지 한국어로 보여준다.

**Tech Stack:** Python 3.13, FastAPI frontend API adapter, Postgres SQL read model, Next.js App Router, unittest.

---

## Task 1: Contract And Fixture

**Files:**
- Create: `docs/tasks/trading-readiness-cockpit/contract.md`
- Create: `docs/tasks/trading-readiness-cockpit/handoff.md`
- Modify: `docs/api/frontend/contract-index.json`
- Create: `docs/api/frontend/examples/trading-readiness.json`

**Steps:**
- Add task contract with boundaries: no broker submission, no write API, no secrets.
- Add frontend contract endpoint `GET /api/trading/readiness`.
- Add fixture example covering blocked default state.

## Task 2: Backend Read Model

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/frontend-api.ts`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add `build_live_trading_readiness_response`.
- Add `render_frontend_trading_readiness_state_sql`.
- Read only these canonical tables: `trading.broker_boundary`, `trading.account_permission`, `trading.order_limit_policy`, `trading.kill_switch_state`, `trading.paper_validation_run`, `trading.order_intent_audit`, `portfolio.portfolio`.
- Redact secrets: expose only `secret_configured: boolean`.
- Add tests for DTO shape and SQL read-only guarantees.

## Task 3: Frontend Page

**Files:**
- Create: `apps/web/src/app/trading-readiness/page.tsx`
- Modify: `apps/web/src/app/layout.tsx`
- Modify: `apps/web/src/app/paper-trading/page.tsx`
- Modify: `apps/web/src/app/globals.css`
- Modify: `apps/web/src/lib/korean-labels.ts`

**Steps:**
- Add navigation item “거래 안전”.
- Add page hero explaining this is not an order screen.
- Show safety gates, broker/account/limit/kill switch/paper validation/audit state.
- Add link from paper trading page to trading readiness.

## Task 4: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_trading_safety`
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task trading-readiness-cockpit`
- Browser snapshot for `http://127.0.0.1:3001/trading-readiness`
- `git diff --check`
