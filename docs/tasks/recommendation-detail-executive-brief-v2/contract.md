# recommendation-detail-executive-brief-v2 Contract

## Task Request

- request: Continue the recommendation detail UX/UI renewal after `recommendation-detail-position-ux-v1`.
- request: Improve `/recommendations/recommendation-471` so the top of the page reads like a professional investment research brief, not an operational log.
- request: Keep the Bloomberg/Koyfin/YCharts-style principle: first screen should answer what the recommendation is, whether we own it, what price/valuation context says, what evidence is weak, and whether trading remains blocked.

## Goal

- goal: Add a concise executive decision brief near the top of recommendation detail.
- goal: The brief should summarize:
  - recommendation and score,
  - holding status and average cost availability,
  - target/recommended weight,
  - valuation status/upside/margin of safety when available,
  - professional evidence coverage and blockers,
  - paper validation and real-order boundary.

## Mutable Surface

- mutable surface: `apps/web/src/app/recommendations/[recommendationId]/page.tsx`
- mutable surface: `apps/web/src/components/recommendation-executive-brief.tsx`
- mutable surface: `apps/web/src/components/recommendation-executive-brief.module.css`
- mutable surface: `apps/web/src/components/recommendation-position-reality.tsx`
- mutable surface: `docs/tasks/recommendation-detail-executive-brief-v2/`

## Invariants

- No recommendation score weight changes.
- No benchmark, portfolio position, outcome, paper validation, or broker/order mutation.
- No API contract/schema change unless strictly required. Prefer frontend view-model composition from existing detail payload.
- Investor-facing copy must avoid `pipeline`, `runner`, `artifact`, raw DB field names, and English-only internal status codes.

## Verification Commands

- verification command: `cd apps/web && npm test -- --run`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `bash scripts/verify_frontend_api_contract.sh`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-executive-brief-v2`
- verification command: Playwright smoke for `/recommendations/recommendation-471` at 375px, 768px, 1280px.

## Acceptance Criteria

- `/recommendations/recommendation-471` shows a high-level “투자 판단 요약” before the long evidence sections.
- The brief clearly says `SPY` is not currently held and therefore average cost is not available.
- The brief separates `recommended weight` from actual holding weight.
- The brief states that real orders remain blocked/read-only.
- No investor-facing top summary text contains internal operation terms.
