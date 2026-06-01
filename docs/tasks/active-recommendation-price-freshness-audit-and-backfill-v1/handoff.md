# active-recommendation-price-freshness-audit-and-backfill-v1 Handoff

## Current Status

- status: implemented_and_ec2_smoked
- started_at: 2026-06-01
- current status: API payload, open gate detail, frontend data-health card, DTO typing, EC2 deploy, and provider backfill are complete.
- completed: active recommendation price freshness now appears in `/api/data-health` and `/data-health`.
- completed: EC2 backfill refreshed all stale active recommendation symbols to the latest global price date.

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
- 2026-06-01 local: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task active-recommendation-price-freshness-audit-and-backfill-v1` passed.
- 2026-06-01 EC2: deployed commit `cdc46e9`.
- 2026-06-01 EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter -v` passed, 89 tests.
- 2026-06-01 EC2: `cd apps/web && npm run typecheck` passed.
- 2026-06-01 EC2: `cd apps/web && npm run build` passed.
- 2026-06-01 EC2: `market-price-free-backfill-run` completed with `requested_symbol_count=12`, `succeeded_symbol_count=12`, `failed_symbol_count=0`, `total_bar_count=1111`, `provider_request_count=12`, `budget_remaining_after=12`.
- 2026-06-01 EC2: refreshed symbols `QUBT`, `SPY`, `TGT`, `TSLA`, `XOM`, `EROK`, `FANG`, `GILD`, `GOOG`, `INTU`, `LDOS`, `LLY`.
- 2026-06-01 EC2: `/api/data-health.active_recommendation_price_freshness.status=fresh`, `attention_required=false`, `active_symbol_count=23`, `fresh_symbol_count=23`, `stale_symbol_count=0`, `missing_symbol_count=0`, `global_latest_trade_date=2026-05-29`.
- 2026-06-01 EC2: `/data-health` renders `추천 종목 가격`, `추천에 쓰는 가격이 최신인지 확인`, `최신성 확인`, `23/23개 최신`.

## Remaining

- remaining: `cycle_ai_quality_audit_attention` still reports one duplicate syndicated oil-reserve title. This is not an active recommendation price issue.
- remaining: `data_operations_artifact_runner` still reports stale daily decision/performance/portfolio jobs from 2026-05-29. This appears to be a cadence/weekend or pre-market-day freshness policy issue and should be handled in a separate scheduler/data-health cadence task.

## Next Step

- exact next step: decide whether to treat weekend/pre-close daily job stale status as a false-positive data-health policy issue, then implement a cadence-aware stale policy task if needed.
