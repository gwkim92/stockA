# Financial Forecast And Scenario Inputs V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add explicit revenue, margin, CAPEX, and FCF forecast inputs behind DCF/scenario valuation without changing recommendation weights.

**Architecture:** Store deterministic scenario/year forecast rows in Postgres as canonical evidence. Valuation snapshots reference these rows in assumptions JSON, and the frontend live adapter converts them into Korean forecast evidence for stock, recommendation, and thesis detail pages.

**Tech Stack:** Python backend CLI, Postgres SQL migrations/upserts, FastAPI read DTO through live adapter, Next.js TypeScript UI.

---

### Task 1: Forecast Input Storage

**Files:**
- Create: `db/migrations/0024_financial_forecast_inputs.sql`
- Modify: `tests/test_professional_equity_analysis.py`

**Steps:**
1. Add `market.financial_forecast_input` with scenario/year rows and read-only evidence columns.
2. Add migration assertions that the table, unique key, and safety constraints exist.
3. Run `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis`.

### Task 2: Backend Runner

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Modify: `src/stockanalysis/operations/cli.py`
- Modify: `tests/test_professional_equity_analysis.py`
- Modify: `tests/test_data_operations_cli.py`

**Steps:**
1. Add preview/upsert SQL and `run_financial_forecast_inputs`.
2. Add CLI command `financial-forecast-inputs-run`.
3. Verify dry-run and execute guardrails, including `recommendation_scoring_mutated=false`.
4. Run targeted Python tests.

### Task 3: Valuation Integration

**Files:**
- Modify: `src/stockanalysis/operations/professional_equity_analysis.py`
- Modify: `tests/test_professional_equity_analysis.py`

**Steps:**
1. Join latest forecast inputs in valuation snapshot SQL.
2. Add forecast evidence to DCF-lite/scenario `assumptions_json`.
3. Keep existing valuation output shape backward compatible.
4. Run valuation snapshot tests.

### Task 4: Frontend Evidence Visibility

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/components/valuation-target-range-card.tsx`
- Modify: `tests/test_frontend_live_adapter.py`

**Steps:**
1. Convert forecast assumptions JSON into `forecast_evidence` DTO fields.
2. Render scenario/year forecast rows in Korean on the shared valuation card.
3. Verify stock/recommendation/thesis DTO shapes and typecheck/build.

### Task 5: Docs, Verification, Deployment

**Files:**
- Modify: `docs/project-execution-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `scripts/verify_project_execution_roadmap.sh`
- Modify: `docs/tasks/financial-forecast-and-scenario-inputs-v1/handoff.md`
- Create: `docs/tasks/financial-forecast-and-scenario-inputs-v1/review.md`

**Steps:**
1. Run local verification commands from the contract.
2. Commit and push.
3. Deploy to EC2 and run API/route smoke.
4. Record EC2 evidence and set next task.
