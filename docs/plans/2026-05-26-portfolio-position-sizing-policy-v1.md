# Portfolio Position Sizing Policy V1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a read-only position sizing envelope that helps decide whether each holding should be reduced, held, watched, or blocked from adding until evidence is stronger.

**Architecture:** The first slice does not add schema. The FastAPI live adapter composes existing portfolio coverage, risk budget guardrail, valuation snapshot, recommendation professional components, and equity research artifact state into a DTO. The Next.js cockpit renders the DTO on `/portfolio/coverage`.

**Tech Stack:** Python live adapter, Postgres SQL JSON projection, unittest, Next.js Server Components, TypeScript DTO types.

---

### Task 1: Document Contract

**Files:**
- Create: `docs/tasks/portfolio-position-sizing-policy-v1/contract.md`
- Create: `docs/tasks/portfolio-position-sizing-policy-v1/handoff.md`
- Create: `docs/plans/2026-05-26-portfolio-position-sizing-policy-v1.md`

**Steps:**
- Record the read-only scope and guardrails.
- State that recommendation weights and broker submit are not changed.

### Task 2: API Context Lookup

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add `render_frontend_portfolio_position_sizing_context_state_sql`.
- Add loader and call it from `build_live_portfolio_coverage_response`.
- Keep the query read-only and limited to existing portfolio snapshot holdings.

### Task 3: Position Sizing Review DTO

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `apps/web/src/lib/types.ts`

**Steps:**
- Add `risk_budget.position_sizing_review`.
- Include summary, candidate rows, evidence gaps, and read-only boundary flags.
- Unit-test candidate review status, representative candidate fields, and order boundary.

### Task 4: Portfolio Coverage UX

**Files:**
- Modify: `apps/web/src/app/portfolio/coverage/page.tsx`
- Modify: `apps/web/src/lib/korean-labels.ts`

**Steps:**
- Add a Korean section that explains position sizing review in investor language.
- Show review band, current/benchmark/active weight, evidence state, and rationale.
- Avoid developer wording and avoid implying automatic orders.

### Task 5: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task portfolio-position-sizing-policy-v1`

**EC2 Smoke:**
- Pull latest code on EC2.
- Restart FastAPI/Next.js services.
- Confirm `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-26` includes `position_sizing_review`.
- Confirm `/portfolio/coverage` renders the Korean section through the local tunnel.
