# Implementation Plan

## Steps

1. Add task contract, plan, handoff, and review docs.
2. Add event list and theme detail fixture DTO examples.
3. Extend contract index, TypeScript types, and frontend API client.
4. Add `/events` and `/themes/[themeKey]` Server Component routes.
5. Link `/cycles` cards to theme detail where supported.
6. Update docs, tests, and verification scripts.
7. Run verification and publish the branch.

## Verification

```bash
bash scripts/verify_frontend_detail_routes.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task frontend-event-theme-explorer
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
