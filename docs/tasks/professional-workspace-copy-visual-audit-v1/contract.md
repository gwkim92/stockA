# professional-workspace-copy-visual-audit-v1 Contract

## Task Request

- request: Improve the visible UX writing, visual hierarchy, and repeated card language across the investment workspace so the product reads like a professional research cockpit instead of an operations log.
- context: The current UI has too many repeated "확인" phrases, generic same-looking cards, weak empty states, and investor-facing pages that still feel like backend status surfaces.

## Goal

- goal: The main investment pages should clearly show what to look at first, why it matters, and where the evidence flows next, using professional Korean copy and stronger visual hierarchy without changing data contracts, scoring, or broker/order boundaries.

## Scope

- Tighten the shared visual system for decision cards, empty states, section headings, news evidence cards, and review rails.
- Replace developer/worker-style copy in visible user surfaces with investor-facing Korean language.
- Preserve route structure and existing API contracts.
- Preserve recommendation scoring, outcome calibration, benchmark definitions, portfolio positions, broker/order boundaries, and schema.

## Target Pages

- `/`
- `/market-map`
- `/cycle-map`
- `/recommendations`
- `/paper-trading`
- `/ai-evidence`
- `/ai-evidence/[evidenceId]`
- `/ai-evidence/blocked`
- `/ai-evidence/results`
- `/data-health`
- `/stocks/[symbol]`
- `/recommendations/[recommendationId]`
- `/intelligence`
- `/portfolio/coverage`

## Design Direction

- Intent: a Korean investor opens the system to decide what needs attention today, not to read backend job names.
- Tone: professional research desk, dense but legible, restrained, not generic SaaS cards.
- Signature: a decision rail that traces market condition → evidence → symbol → recommendation → execution boundary.
- Reject: identical metric card grids, repeated "확인" copy, visible runner/pipeline/artifact wording in investor surfaces.

## Non-Goals

- No data model changes.
- No scoring weight changes.
- No broker submit or live order path changes.
- No new paid provider or AI runtime change.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/globals.css`
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/market-map/page.tsx`
  - `apps/web/src/app/cycle-map/page.tsx`
  - `apps/web/src/app/intelligence/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/ai-evidence/[evidenceId]/page.tsx`
  - `apps/web/src/app/ai-evidence/blocked/page.tsx`
  - `apps/web/src/app/ai-evidence/results/page.tsx`
  - `apps/web/src/app/data-health/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/app/portfolio/coverage/page.tsx`
  - `apps/web/src/components/news-event-card.tsx`
  - `apps/web/src/components/news-title-block.tsx`
  - `docs/tasks/professional-workspace-copy-visual-audit-v1/*`

Do not mutate recommendation scoring, benchmark definitions, portfolio positions, DB schema, broker/order submit paths, secrets, or deployment configuration.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `python3 -m compileall -q src tests`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-workspace-copy-visual-audit-v1`
- verification command: rendered route smoke for target pages.
- verification command: visible text scan for unwanted internal terms and server error copy.
