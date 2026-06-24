# professional-workspace-hierarchy-expansion-v1 Contract

## Task Request

- request: Extend the professional workspace visual hierarchy from the previous task to `/market-map`, `/cycle-map`, `/recommendations`, `/paper-trading`, and `/ai-evidence`.
- request: Make each target page show the primary decision, supporting checks, and safety boundary with the same visual grammar.

## Goal

- goal: The target pages should no longer feel like separate ad-hoc dashboards. Each page should begin with a clear decision brief where the first card is the primary action/read, secondary cards are support checks, and internal execution wording is kept out of the user-facing decision surface.

## Mutable Surface

- mutable surface:
  - `apps/web/src/app/market-map/page.tsx`
  - `apps/web/src/app/cycle-map/page.tsx`
  - `apps/web/src/app/recommendations/page.tsx`
  - `apps/web/src/app/paper-trading/page.tsx`
  - `apps/web/src/app/ai-evidence/page.tsx`
  - `apps/web/src/app/globals.css`
  - `docs/tasks/professional-workspace-hierarchy-expansion-v1/*`

## Scope

- Apply existing `workspace-brief` and `workspace-command-grid` patterns to the target page hero sections.
- Make the first decision card visually dominant on each target page.
- Remove obvious internal execution wording from visible user copy where encountered.
- Preserve the existing data, links, and route behavior.

## Non-Goals

- No DB schema changes.
- No API payload changes.
- No recommendation scoring weight changes.
- No benchmark, outcome/evaluation split, portfolio position, scheduler, AWS security group, or broker/order changes.
- No Toss promotion into recommendation/cycle scoring.

## Verification Commands

- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `git diff --check`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task professional-workspace-hierarchy-expansion-v1`
- verification command: Rendered route smoke for `/market-map`, `/cycle-map`, `/recommendations`, `/paper-trading`, `/ai-evidence`, plus existing key pages.

## Acceptance Criteria

- `/market-map`, `/cycle-map`, `/recommendations`, `/paper-trading`, `/ai-evidence` render with `workspace-command-grid` cards at the top.
- The primary decision card is visually larger than secondary cards on desktop.
- Visible text scan has no hits for `canonical`, `shadow`, `pipeline`, `artifact`, `runner`, `fallback`, `LLM`, `human review`, `사람 검토`, `검토 가능`.
- No visible server-component/error-like text appears on the checked route set.
