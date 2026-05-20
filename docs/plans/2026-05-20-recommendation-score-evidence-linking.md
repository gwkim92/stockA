# Recommendation Score Evidence Linking Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Link recommendation score components to concrete event or AI evidence ids so recommendation review can become evidence-ready.

**Architecture:** Keep scoring, schema, benchmark, trading, and scheduler behavior unchanged. Extend the read-only recommendation detail SQL to select a current event/AI evidence anchor for the recommendation instrument, use it for relevant score components, and render links from the recommendation page to the event ledger or AI evidence detail.

**Tech Stack:** Python SQL renderer, frontend live adapter DTOs, Next.js server components, unittest, AWH harness.

---

### Task 1: Harness Contract

**Files:**
- Create: `docs/tasks/recommendation-score-evidence-linking/contract.md`
- Create: `docs/tasks/recommendation-score-evidence-linking/handoff.md`
- Create: `docs/tasks/recommendation-score-evidence-linking/review.md`

**Steps:**
- Define this as a read-only evidence-linking task.
- Exclude recommendation score changes, DB migration, LLM calls, broker/order writes, and scheduler activation.
- Record verification commands.

### Task 2: Backend Evidence Anchor

**Files:**
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Test: `tests/test_frontend_live_adapter.py`

**Steps:**
- Add `recommendation_event_anchor` and `recommendation_evidence_anchor` CTEs to `render_frontend_recommendation_detail_state_sql`.
- Prefer `ai-evidence-{artifact_id}` when available, otherwise use `event-{event_id}`.
- Use the anchor for cycle/event-like score components while preserving market-feature fallbacks.
- Change recommendation links to expose a valid event ledger link rather than an unsupported event detail URL.

### Task 3: Frontend Links

**Files:**
- Modify: `apps/web/src/app/recommendations/[recommendationId]/page.tsx`

**Steps:**
- Link `ai-evidence-*` component ids to `/ai-evidence/{id}`.
- Link `event-*` or `sec-event-*` ids to `/events?symbol={symbol}`.
- Leave non-concrete feature ids as plain text.

### Task 4: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-score-evidence-linking`
- Live API smoke: `/api/recommendations/AAPL-2024-11-01`
- Browser check: `/recommendations/AAPL-2024-11-01`
- `git diff --check`

### Done Criteria

- Recommendation detail API returns at least one event/AI evidence-linked score component when source evidence exists.
- Recommendation evidence review no longer warns solely because score components lack concrete evidence ids.
- Recommendation page links concrete evidence ids to a valid screen.
- Handoff/review contain fresh verification evidence.
