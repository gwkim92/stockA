# Portfolio Risk Budget Rebalance Candidate Review Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Convert full benchmark drift outliers into review-only rebalance candidates that are visible in API and UI without changing recommendation weights or enabling orders.

**Architecture:** Reuse the latest persisted `portfolio_risk_budget_guardrail` score JSON as the source of truth. Add a deterministic DTO transformation in the frontend live adapter, then render the same candidate list in portfolio coverage, paper trading, and trading readiness screens.

**Tech Stack:** Python backend DTO adapter, FastAPI read-only API, Next.js Server Components, TypeScript DTO types, unittest.

---

### Task 1: Backend DTO Candidate Builder

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Write a unit test that feeds `benchmark_drift.top_active_positions` with `TSLA`, `MSFT`, `AAPL`, and an underweight row.
- Assert the returned `portfolio_risk_budget_guardrail.rebalance_candidate_review.candidates` includes direction, severity, rationale, and `order_boundary=read_only_no_order`.
- Implement `_build_benchmark_rebalance_candidate_review_payload`.
- Attach it to `_build_trading_risk_budget_guardrail_payload`.
- Reuse it in portfolio coverage risk budget payload by passing the trading guardrail into the coverage builder.

### Task 2: TypeScript Contract

**Files:**
- Modify: `apps/web/src/lib/types.ts`

**Steps:**
- Add `BenchmarkRebalanceCandidate` and `BenchmarkRebalanceCandidateReview` shapes.
- Extend `TradingReadinessData.portfolio_risk_budget_guardrail`.
- Extend `PortfolioCoverageData.risk_budget`.
- Keep fields nullable only where source data can be absent.

### Task 3: Portfolio Coverage UI

**Files:**
- Modify: `apps/web/src/app/portfolio/coverage/page.tsx`

**Steps:**
- Render a dedicated “벤치마크 대비 리밸런싱 검토” section near the stored guardrail block.
- Show active share, source, candidate count, top candidates, direction, active weight, rationale, and read-only boundary.
- Use clear Korean writing: “주문 후보” 금지, “검토 후보”로 통일.

### Task 4: Paper/Trading Safety UI

**Files:**
- Modify: `apps/web/src/app/paper-trading/page.tsx`
- Modify: `apps/web/src/app/trading-readiness/page.tsx`

**Steps:**
- Add compact candidate cards tied to the existing risk guardrail section.
- Explain that the candidates are why paper validation remains blocked by risk budget review.
- Keep all order and broker status indicators blocked/read-only.

### Task 5: Verification And Handoff

**Files:**
- Modify: `docs/tasks/portfolio-risk-budget-rebalance-candidate-review/handoff.md`
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`

**Steps:**
- Run focused adapter tests.
- Run full unittest/compile/frontend typecheck/build.
- Run route/API smoke locally through `127.0.0.1:13000` after EC2 deploy.
- Update handoff with exact run IDs and smoke evidence.
- Commit and push.
