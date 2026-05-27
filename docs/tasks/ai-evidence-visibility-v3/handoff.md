# ai-evidence-visibility-v3 Handoff

## Status

- status: implemented_local
- started_at: 2026-05-27
- current status: local implementation is complete and targeted verification passed; EC2 deploy and smoke are next.
- completed: API visibility trace payload, frontend trace board, Korean labels, DTO typing, targeted backend test, typecheck, build.
- in progress: EC2 deploy and smoke.

## Current Decision

- Keep the screen read-only.
- Show AI review results as evidence trace, not as a manual approval workflow.
- Do not add approval/rejection buttons until audit write API and RBAC write policy exist.

## Next Step

- exact next step: add `visibility_trace` to `/api/ai-evidence/{id}` and render it on `/ai-evidence/{id}`.

## Verification So Far

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall -q src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`

## Risks

- Recommendation linkage comes from the separately loaded evidence neighborhood. The API trace can state the candidate symbol, but the final linked recommendation count is filled on the frontend from neighborhood data.
