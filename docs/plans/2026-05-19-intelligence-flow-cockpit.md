# Intelligence Flow Cockpit Implementation Plan

**Goal:** Make the site show the full analysis chain: event/news-like input, AI evidence, theme/cycle signal, recommendation, thesis, portfolio holding review, and paper-trading safety context.

**Architecture:** Reuse existing read-only API calls from the Next.js server component layer. Do not add a backend endpoint yet because the necessary DTOs already exist and this slice is about operator comprehension.

---

## Task 1: Task Contract

**Files:**
- Create: `docs/tasks/intelligence-flow-cockpit/contract.md`
- Create: `docs/tasks/intelligence-flow-cockpit/handoff.md`

**Steps:**
- Record that this task is a UI integration and wording slice.
- Record that no broker writes, scoring formula changes, or new LLM calls are included.

## Task 2: Integrated Analysis Page

**Files:**
- Create: `apps/web/src/app/intelligence/page.tsx`

**Steps:**
- Fetch events, cycle states, the annual-reporting theme detail, portfolio coverage, and paper trading preview in parallel.
- Render where to see signal, recommendation, holding review, and AI evidence.
- Render event rows that connect event -> AI/source -> theme/cycle -> recommendation/thesis -> holding/paper review.
- Explain that AI output is evidence metadata, not a direct buy/sell decision.

## Task 3: Navigation And Home Entry

**Files:**
- Modify: `apps/web/src/app/layout.tsx`
- Modify: `apps/web/src/app/page.tsx`

**Steps:**
- Add `/intelligence` to global navigation near dashboard/data health.
- Add a home CTA to open the analysis map.

## Task 4: Styling

**Files:**
- Modify: `apps/web/src/app/globals.css`

**Steps:**
- Add a readable, editorial trace layout.
- Keep the existing Korean cockpit visual language and mobile behavior.

## Task 5: Verification

**Commands:**
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`
- `curl -fsS -o /private/tmp/stockanalysis-runtime/intelligence.html -w '%{http_code}' http://127.0.0.1:3001/intelligence`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task intelligence-flow-cockpit`
- `git diff --check`
