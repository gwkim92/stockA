# openai-admin-cost-visibility-v1 Handoff

## Status

- completed: Admin Costs API refresh CLI, cached provider health payload, and `/data-health`/`/admin/ai-agents` visibility are implemented.

## Current Decision

- Use only official OpenAI Admin Costs API.
- Store a secret-free cached status artifact outside the repository.
- Keep `remaining_balance_usd` null because official Costs API returns spend, not remaining prepaid balance.
- Frontend request rendering reads cache only and never calls OpenAI directly.
- New CLI: `stockanalysis-operations openai-admin-cost-refresh-run --env-file <repo-outside-env> --execute`.
- New env: `STOCKANALYSIS_OPENAI_COST_STATUS_PATH`.
- Screen wording separates `남은 잔액` from `최근 비용`.

## Verification

- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_data_operations_cli tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m compileall src tests`
- passed: `cd apps/web && npm run typecheck`
- passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest discover -s tests`
- passed: `cd apps/web && npm run build`

## Next Step

- exact next step: deploy commit to EC2, copy `OPENAI_ADMIN_API_KEY` into repo-outside runtime env files without printing it, run `openai-admin-cost-refresh-run --execute`, restart services, and smoke `/data-health` plus `/admin/ai-agents`.

## Boundaries

- No key exposure.
- No undocumented billing dashboard scraping.
- No recommendation scoring or broker/order change.
