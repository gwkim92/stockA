# active-recommendation-price-freshness-audit-and-backfill-v1 Handoff

## Current Status

- status: implementation_verified_locally
- started_at: 2026-06-01
- current status: API payload, open gate detail, frontend data-health card, DTO typing, and focused tests are implemented locally; EC2 deploy and provider backfill are next.
- in progress: EC2 deploy and provider backfill remain.

## Context

- EC2 data audit found no current AI/news corruption, but active recommendation symbols had stale price bars compared with the global latest `market.daily_price_bar` date.
- Affected symbols observed before implementation included `QUBT`, `SPY`, `TGT`, `TSLA`, `XOM`, `EROK`, `FANG`, `GILD`, `GOOG`, `INTU`, `LDOS`, `LLY`.
- This affects recommendation freshness, outcome calibration, and paper validation interpretation, but must not mutate recommendation scoring or order state.

## Decisions

- Use the existing `market-price-free-backfill-run` runner for EC2 backfill.
- Treat active recommendation price freshness as an operational data-quality gate, not a trading decision.
- Keep `order_boundary=read_only_no_order`, `automatic_order_allowed=false`, `broker_submit_allowed=false`.

## Verification Log

- 2026-06-01 local: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter -v` passed, 89 tests.
- 2026-06-01 local: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests` passed.
- 2026-06-01 local: `cd apps/web && npm run typecheck` passed.
- 2026-06-01 local: `cd apps/web && npm run build` passed.
- 2026-06-01 local: `git diff --check` passed.

## Next Step

- exact next step: commit and push this task, deploy it to EC2, then run `market-price-free-backfill-run` for the active recommendation stale-symbol watchlist and confirm `/api/data-health.active_recommendation_price_freshness`.
