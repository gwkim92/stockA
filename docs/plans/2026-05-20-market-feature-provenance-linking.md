# Market Feature Provenance Linking Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make recommendation market/rank score components traceable to the exact feature snapshot, strategy universe rank, and pipeline run that produced them.

**Architecture:** Keep the recommendation scoring formula, schema, benchmark, LLM behavior, broker boundary, and scheduler behavior unchanged. Extend the read-only recommendation detail SQL and DTO mapping so each score component carries a compact provenance object, then render that provenance on the recommendation detail page in Korean.

**Tech Stack:** Python SQL renderer, frontend live adapter DTOs, Next.js server components, TypeScript DTOs, unittest, AWH harness.

---

### Task 1: Harness Contract

**Files:**
- Create: `docs/tasks/market-feature-provenance-linking/contract.md`
- Create: `docs/tasks/market-feature-provenance-linking/handoff.md`
- Create: `docs/tasks/market-feature-provenance-linking/review.md`

**Steps:**
- Define this as a read-only provenance task.
- Exclude scoring formula changes, schema changes, provider calls, broker/order writes, and scheduler activation.
- Record verification commands and remaining risk.

### Task 2: Backend Provenance DTO

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add market feature provenance CTEs to `render_frontend_recommendation_detail_state_sql`.
- Map `momentum_score` to `return_since_first_observation`.
- Map `short_term_score` to `return_1d`.
- Map `rank_score` to the selected strategy universe rank/batch instead of pretending it is a market feature.
- Add a `provenance` object to each score component payload.
- Add a recommendation evidence review gate for market/rank provenance.

### Task 3: Frontend Rendering

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `apps/web/src/lib/korean-labels.ts`
- Modify: `apps/web/src/app/recommendations/[recommendationId]/page.tsx`

**Steps:**
- Extend the TypeScript recommendation score component type with provenance.
- Render source type, feature code/name, source run, observation window, and universe rank in readable Korean.
- Keep actual evidence links unchanged: AI evidence and event ids link to real screens; market feature lineage renders inline.

### Task 4: Contract Example

**Files:**
- Modify: `docs/api/frontend/examples/recommendation-detail.json`

**Steps:**
- Update the example recommendation detail payload to show market feature and rank provenance.
- Keep response version unchanged because this is additive.

### Task 5: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task market-feature-provenance-linking`
- Live API smoke: `/api/recommendations/AAPL-2024-11-01`
- Browser check: `/recommendations/AAPL-2024-11-01`
- `git diff --check`

### Done Criteria

- Recommendation detail API exposes provenance for market feature score components.
- `rank_score` is clearly labeled as strategy universe rank provenance, not a price feature.
- Recommendation page shows where the score inputs came from in human-readable Korean.
- Handoff/review contain fresh verification evidence.
