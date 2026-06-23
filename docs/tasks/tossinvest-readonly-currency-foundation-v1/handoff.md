# TossInvest Readonly Currency Foundation V1 Handoff

## Status

- completed: TossInvest read-only currency foundation is implemented locally and passed task readiness checks.

## Current Decisions

- Toss integration is read-only and writes to `Toss Real Readonly` by default.
- Base currency for the Toss portfolio is KRW; holdings retain native currency values.
- FX evidence is stored in `market.fx_rate_snapshot`; position base values remain in existing columns.
- Order submit/modify/cancel are disabled stubs only.
- No scheduler is activated in V1.

## Guardrails

- Do not log Toss client secret, access token, account sequence/account number, or Authorization headers.
- Do not call Toss order endpoints.
- Do not change recommendation weights, benchmarks, or broker submit boundary.

## Verification Notes

- `bash scripts/verify_tossinvest_readonly_currency_foundation.sh`
- `PYTHONPATH=src /tmp/stockanalysis-tossinvest-venv/bin/python -m unittest discover -s tests`
- `bash scripts/verify_migrations.sh`
- `bash scripts/verify_frontend_api_contract.sh`
- `cd apps/web && npm run typecheck`
- `cd apps/web && npm run build`

## Residual Risk

- No live Toss credential/API smoke was run in this environment.
- No scheduler activation was added in V1.
- `npm install` reported existing audit findings; dependency remediation is outside this task.

## Exact Next Step

- exact next step: Review the branch diff, then commit and deploy only if this read-only Toss integration scope is approved.
