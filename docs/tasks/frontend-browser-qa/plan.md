# Implementation Plan

## Steps

1. Inspect current working tree and running local servers.
2. Run browser smoke for cockpit and detail routes.
3. Fix static icon 404 and review queue text overlap.
4. Capture Playwright screenshots under ignored `output/playwright/`.
5. Update task handoff/review docs.
6. Run verification script and AWH verification.
7. Commit and push the browser QA fix branch.

## Verification

```bash
bash scripts/verify_frontend_detail_routes.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-browser-qa
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
