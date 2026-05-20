# Free Market Budget Frontend Visibility

This task exposes the local Alpha Vantage free-tier market data budget ledger in read-only data-health surfaces.

The API must return only sanitized budget status. It must not expose provider keys, bearer tokens, DB URLs, or absolute ledger paths.

## Implemented Behavior

- `/api/data-health` now includes `data.provider_budget`.
- `provider_budget` reports:
  - provider name
  - configuration/ledger status
  - budget date
  - daily budget
  - used request count
  - remaining request count
  - latest runner status and provider request count
- `apps/web` renders a `Free Provider Budget` card on `/data-health`.
- Local runtime reads the ledger path from `STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH`.

## Local Runtime

- FastAPI: `http://127.0.0.1:8787`.
- Next.js: `http://127.0.0.1:3001`.
- Current smoke result: `alpha_vantage`, `status=configured`, `remaining_request_count=1`, `daily_budget=1`, latest runner `provider_request_count=0`.

## Guardrails

- No positive-budget provider call was executed in this task.
- No ledger path or secret is returned by the API.
- No write endpoint was added.
