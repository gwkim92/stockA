# cross-asset-etf-watchlist-price-refresh-v1 Handoff

## Status

- current status: implemented locally; EC2 smoke pending.

## Current Status

- 완료:
  - local implementation and targeted verification are complete.
  - EC2 deploy/smoke is complete.
- 진행 중:
  - none.
- 막힌 점:
  - none currently.

## Completed

- Added `cross_asset_instrument_price_symbols()` to derive the cross-asset ETF/rates/credit ETF price watchlist from the canonical indicator registry.
- Added `cross-asset-market-price-refresh` to `cross-asset-daily` before direct provider fetch and indicator observation sync.
- The new step writes a repo-outside runtime watchlist and calls existing `market-price-free-backfill-run`.
- The step uses the existing provider budget ledger, `--skip-if-fresh`, `--allow-symbol-failures`, and conservative free-tier bounds:
  - `--daily-budget 80`
  - `--max-requests-per-run 24`
  - `--throttle-seconds 8.0`
  - `--outputsize 120`
- Added data-health cadence metadata for `cross-asset-market-price-refresh-daily`.
- Added tests for watchlist derivation and cross-asset profile step ordering.
- Added canonical instrument bootstrap to `free-provider-capacity-registry-run` so missing ETF instruments are inserted before price upsert.

## Verification

- passed: `PYTHONPATH=src python3 -m unittest tests.test_cross_asset_market tests.test_operating_data_orchestrator tests.test_operating_data_profile_scheduler`
- passed: `PYTHONPATH=src python3 -m compileall src tests`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task cross-asset-etf-watchlist-price-refresh-v1`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_cross_asset_market tests.test_operating_data_orchestrator tests.test_operating_data_profile_scheduler`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`
- passed on EC2: `operating-data-run --profile cross-asset-daily --execute --timeout-seconds 1800`, `run_status=completed`, `failed_step_count=0`.
- passed on EC2: `cross-asset-market-price-refresh` artifact `20260605T163223Z_cross-asset-market-price-refresh-daily`, `requested_symbol_count=18`, `succeeded_symbol_count=12`, `failed_symbol_count=0`, `skipped_symbol_count=6`, `provider_request_count=12`, `symbol_failures_allowed=true`.
- passed on EC2: `/api/data-health.cross_asset_market_regime` improved from `fresh_indicator_count=20`, `missing_indicator_count=18` before this task to `fresh_indicator_count=37`, `missing_indicator_count=1`, `stale_indicator_count=1`, `shock_indicator_count=19`, `news_indicator_link_count=44`, `recommendation_component_count=96`, `non_zero_weight_component_count=0`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.

## Remaining Work

- exact next step: decide how to handle the one remaining missing/stale pair: `XAG_USD` Twelve Data symbol fallback and stale FRED `USD_BROAD_INDEX`.
- Add frontend `/market-map` and stock/recommendation detail cross-asset sections after remaining provider quality policy is explicit.

## Boundaries

- Recommendation weights remain unchanged.
- Broker/order flow remains blocked.
- No paid provider was added.
- `XAG_USD` symbol/provider fallback remains outside this task.
