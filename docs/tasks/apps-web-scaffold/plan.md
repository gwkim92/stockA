# Implementation Plan

## Steps

1. Create task contract, plan, handoff, and review docs.
2. Scaffold `apps/web` with Next.js App Router, TypeScript, and CSS.
3. Add typed frontend fixture API client.
4. Add initial routes for dashboard, remediation, data health, and cycles.
5. Add distinctive responsive cockpit styling.
6. Update frontend verification scripts so earlier tasks remain valid after scaffold exists.
7. Add `scripts/verify_apps_web_scaffold.sh`.
8. Add docs and README/verification plan updates.
9. Run final verification and record results.

## Design Decisions

- Use React Server Components for read views.
- Fetch fixture payloads from `STOCKANALYSIS_FRONTEND_API_BASE_URL`.
- Keep first scaffold read-only and fixture-only.
- No Tailwind or UI framework yet. Use repo-local CSS tokens to keep the visual direction explicit.

## Verification

```bash
bash -n scripts/verify_apps_web_scaffold.sh
bash scripts/verify_apps_web_scaffold.sh
bash scripts/verify_frontend_fixture_server.sh
PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task apps-web-scaffold
rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S
```
