# Implementation Plan

## Steps

1. Add task contract, plan, handoff, and review docs.
2. Extend frontend API types and client functions for recommendation, thesis, and portfolio coverage DTOs.
3. Add `/recommendations/[recommendationId]` route.
4. Add `/theses/[thesisId]` route.
5. Add `/portfolio/coverage` route.
6. Add CSS patterns for detail pages.
7. Add `scripts/verify_frontend_detail_routes.sh`.
8. Update docs and run verification.

## Verification

```bash
bash -n scripts/verify_frontend_detail_routes.sh
bash scripts/verify_frontend_detail_routes.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-detail-routes
```
