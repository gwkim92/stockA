# Implementation Plan

## Steps

1. Add task contract, plan, handoff, and review docs.
2. Start fixture server and Next app.
3. Use browser automation to inspect key routes and capture screenshots.
4. Record findings in `report.md`.
5. Fix small UI issues if found.
6. Run verification commands and update handoff/review.
7. Publish the branch through PR.

## Verification

```bash
bash scripts/verify_frontend_detail_routes.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-browser-visual-qa
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
