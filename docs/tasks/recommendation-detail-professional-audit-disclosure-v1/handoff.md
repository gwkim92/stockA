# recommendation-detail-professional-audit-disclosure-v1 Handoff

## Status

- completed: professional evidence audit section extracted into a dedicated investor-facing disclosure panel.
- completed: layer-by-layer professional audit checks now start collapsed and remain available behind details disclosure.
- completed: mixed English/internal status labels in the panel are translated or hidden behind investor-facing Korean copy.
- 시작 커밋: `f48889ca`.

## Context

- Previous task collapsed score audit details into a dedicated panel.
- Remaining UX issue: professional evidence audit still renders detailed layer checks directly inside the oversized recommendation detail page.
- This task should extract the professional audit rendering and preserve all details behind progressive disclosure.

## Implementation Notes

- Added `RecommendationProfessionalAuditPanel` with CSS-module styling and `recommendation-professional-audit-model` copy/status helpers.
- Replaced the inline professional audit section in `/recommendations/[recommendationId]` with the new panel.
- Preserved source blocker, coverage, missing layers, layer checks, score policy, and order boundary without changing recommendation scoring or broker/order behavior.
- Browser QA used local latest production Next build on `127.0.0.1:3002` connected to EC2 FastAPI through `127.0.0.1:18787`.

## Verification Evidence

- `cd apps/web && npm test -- --run src/components/recommendation-professional-audit-panel.test.tsx`: passed, 3 tests.
- `cd apps/web && npm test -- --run`: passed, 13 files / 33 tests.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- `bash scripts/verify_frontend_api_contract.sh`: passed.
- `bash scripts/verify_project_execution_roadmap.sh`: passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-detail-professional-audit-disclosure-v1`: passed.
- Browser QA: 375px, 768px, and 1280px had no horizontal overflow, details were collapsed by default, expanded layer checks were visible, `pending`/internal terms were absent, and raw English news title was replaced with Korean fallback copy.

## Next Step

- exact next step: deploy `develop` to EC2, run `/recommendations/recommendation-471` route smoke, and then continue the broader recommendation detail UX reduction if needed.
