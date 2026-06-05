# free-api-cross-asset-news-cycle-integration-v1 Handoff

## Status

- current status: backend foundation implemented and EC2 execute smoke passed. Cross-asset daily now writes provider registry, indicator observations, regime snapshots, news-indicator links, zero-weight recommendation components, and `/api/data-health` visibility.

## Current Status

- completed: backend foundation is implemented locally and deployed to EC2 app path `/opt/stockanalysis/app`.
- completed: migration `0030_cross_asset_market_indicators.sql` was applied on EC2.
- completed: EC2 `macro-weekly` profile ran successfully after expanding FRED defaults.
- completed: EC2 `cross-asset-daily` profile ran successfully with `failed_step_count=0`.
- completed: `/api/data-health` exposes `cross_asset_market_regime`.

## Completed

- Added migration `0030_cross_asset_market_indicators.sql`.
- Expanded default FRED macro series for rates, real rates, inflation expectations, dollar, oil/gas, VIX, and credit spreads.
- Added `stockanalysis.operations.cross_asset_market`.
- Added CLI commands:
  - `free-provider-capacity-registry-run`
  - `cross-asset-indicator-provider-fetch-run`
  - `cross-asset-indicator-ingest-run`
  - `cross-asset-regime-snapshot-run`
  - `indicator-news-linkage-run`
  - `recommendation-cross-asset-components-run`
- Added operating-data cadence entries and `cross-asset-daily` profile.
- Added direct free-provider fetch support for CBOE CSV (`VIX9D`, `VVIX`, `OVX`, `GVZ`) and Twelve Data non-instrument indicators (`XAU/USD`, `XAG/USD`, `BTC/USD`, `ETH/USD`).
- Added support for CBOE single-value CSV format (`DATE,VVIX`, `DATE,OVX`, `DATE,GVZ`) as well as OHLC CSV format.
- Added `--allow-indicator-failures` for provider fetch runs so one free-provider symbol failure is recorded visibly without stopping the whole daily profile.
- Added `/api/data-health.cross_asset_market_regime` payload.
- Added unit tests for provider policy, SQL rendering, regime classification, stale policy, and zero-weight recommendation components.
- Fixed classification node SQL to use the actual `ref.classification_node.code` column instead of nonexistent `node_code`; added regression tests for this DB schema boundary.

## Verification

- passed: `PYTHONPATH=src python3 -m unittest tests.test_cross_asset_market tests.test_operating_data_profile_scheduler`
- passed: `PYTHONPATH=src python3 -m compileall src tests`
- passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli free-provider-capacity-registry-run --dry-run`
- passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli cross-asset-indicator-provider-fetch-run --as-of-date 2026-06-05 --dry-run`
- passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli cross-asset-regime-snapshot-run --as-of-date 2026-06-05 --dry-run`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task free-api-cross-asset-news-cycle-integration-v1`
- passed: `git diff --check`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_cross_asset_market tests.test_operating_data_profile_scheduler`
- passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m compileall -q src tests`
- passed on EC2: apply migration `0030_cross_asset_market_indicators.sql`.
- passed on EC2: `operating-data-run --profile macro-weekly --execute --timeout-seconds 900`, `failed_step_count=0`.
- passed on EC2: `operating-data-run --profile cross-asset-daily --execute --timeout-seconds 1200`, `run_status=completed`, `failed_step_count=0`.
- passed on EC2: `/api/data-health` returned `overall_status=healthy`, `open_gates=[]`, cross-asset related runs all `latest_status=succeeded`:
  - `cross_asset_indicator_provider_fetch` `pipeline-run-3541`
  - `cross_asset_indicator_ingest` `pipeline-run-3542`
  - `cross_asset_regime_snapshot` `pipeline-run-3543`
  - `indicator_news_linkage` `pipeline-run-3544`
  - `recommendation_cross_asset_components` `pipeline-run-3545`
- passed on EC2: `/api/data-health.cross_asset_market_regime` returned `indicator_count=39`, `fresh_indicator_count=20`, `stale_indicator_count=1`, `missing_indicator_count=18`, `shock_indicator_count=12`, `regime_count=10`, `watch_regime_count=1`, `news_indicator_link_count=29`, `linked_news_document_count=21`, `recommendation_component_count=96`, `recommendation_component_recommendation_count=12`, `non_zero_weight_component_count=0`, `recommendation_scoring_mutated=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- passed on EC2: `/` and `/data-health` returned `200` and rendered cross-asset/data-health text after restarting `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.
- not passed: `PYTHONPATH=src python3 -m unittest discover -s tests` on the default Python 3.14 runtime. Observed failures were pre-existing environment/dependency issues: Python 3.14 `pyexpat` load failure for XML-based tests and missing `fastapi` for FastAPI tests. The profile count failures caused by this task were fixed and the targeted scheduler tests now pass.

## Remaining Work

- exact next step: improve coverage for missing/stale cross-asset indicators and then add user-facing `/market-map`.
- Missing/stale indicator follow-up:
  - Sector/index ETF indicators (`DIA`, `HYG`, `IWM`, `LQD`, `QQQ`, `TLT`, `XLB`, `XLC`, `XLE`, `XLF`, `XLI`, `XLK`, `XLP`, `XLRE`, `XLU`, `XLV`, `XLY`) are missing because this slice does not yet run a dedicated cross-asset ETF watchlist price refresh before snapshot. Add these to a budgeted market-price watchlist/profile or a dedicated Twelve Data batch.
  - `XAG_USD` returned a Twelve Data HTTP 404 on EC2. Keep it visible as missing for now; next provider task should validate the correct free symbol or choose a fallback.
  - `USD_BROAD_INDEX` is stale because FRED latest observation was `2026-05-29`; do not impute. Keep stale status visible.
- Add frontend `/market-map` and stock/recommendation detail sections.
- Add Codex OAuth `cross-asset-regime-ai-summary-run` batch after deterministic snapshot quality is verified.

## Boundaries

- Recommendation weights are still zero for cross-asset components.
- No broker/order flow was added.
- No external paid RAG/vector/graph service was added.
