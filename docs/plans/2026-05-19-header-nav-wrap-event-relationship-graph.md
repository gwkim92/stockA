# Header Nav Wrap And Event Relationship Graph Plan

**Goal:** Fix the crowded header so navigation is visible, then add a minimal event relationship graph read-model to make event/news-like analysis easier to follow.

**Architecture:** Keep this read-only. Derive relationships from existing event list data: same source document, same symbol, same theme. This gives useful relationship visibility now without introducing a new schema or paid news provider.

---

## Task 1: Header Wrapping

**Files:**
- Modify: `apps/web/src/app/globals.css`

**Steps:**
- Make `.nav` wrap instead of hiding overflow.
- Keep keyboard focus and mobile behavior.

## Task 2: Event Relationship DTO

**Files:**
- Modify: `apps/web/src/lib/types.ts`
- Modify: `src/stockanalysis/frontend/live_adapter.py`
- Modify: `docs/api/frontend/examples/event-list.json`

**Steps:**
- Add `related_events` to each event payload.
- Relationship types:
  - `same_source_document`
  - `same_symbol`
  - `same_theme`
- Keep payload read-only and deterministic.

## Task 3: UI Display

**Files:**
- Modify: `apps/web/src/app/events/page.tsx`
- Modify: `apps/web/src/app/intelligence/page.tsx`

**Steps:**
- Show related-event relationship cards/chips under each event.
- Explain this is a relationship map, not a recommendation mutation.

## Task 4: Verification

**Commands:**
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_api_adapter tests.test_frontend_live_adapter`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- route smoke for `/events` and `/intelligence`
- AWH verify
- `git diff --check`
