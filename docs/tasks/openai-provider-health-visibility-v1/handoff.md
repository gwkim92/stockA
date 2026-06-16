# openai-provider-health-visibility-v1 Handoff

## Status

- completed: provider health cache, AI 운영 visibility, `/data-health` visibility, and CLI report are implemented.

## Current Decision

- General `OPENAI_API_KEY` is not treated as a reliable remaining-balance source.
- Provider errors become the automatic zero-balance/quota signal.
- Admin Costs API can be added later with `OPENAI_ADMIN_API_KEY`, but frontend request rendering must only read cached health.
- `/admin/ai-agents` shows model/fallback/safety policy and OpenAI provider health.
- `/data-health` shows OpenAI balance/quota/fallback state next to real AI invocation health.
- `stockanalysis-operations openai-provider-health-report` prints the same secret-free state for EC2/operator checks.

## Next Step

- exact next step: run `git diff --check` and AWH verify, then deploy to EC2 from `develop` after commit/push if requested.

## Boundaries

- No key exposure.
- No live OpenAI call from site rendering.
- No recommendation scoring or broker/order change.
- Root `.env` is not accepted as production `--env-file`; data operations env files remain repo-outside by policy.
