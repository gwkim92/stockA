# cross-asset-provider-quality-and-market-map-v1 Handoff

## Status

- current status: implemented locally; develop merge and EC2 smoke pending.

## Current Status

- 완료:
  - Added bounded Twelve Data fallback attempts for `XAG_USD`.
  - Added explicit stale policy evidence for FRED `USD_BROAD_INDEX`.
  - Added live/fixture `/api/market-map` contract and Next.js `/market-map` page.
  - Added home navigation to the new market map.
  - Added regression tests for provider fallback, stale policy SQL, live adapter DTO, fixture contract count, and read-only SQL boundary.
  - Fixed EC2 smoke schema mismatch by reading news publisher from `ingest.data_source.source_name` instead of a non-existent `ingest.source_document.source_name`.
  - Ran EC2 direct provider smoke for `XAG_USD`; Twelve Data candidates `XAG/USD`, `XAGUSD`, and `SILVER` all returned 404, so the policy is to keep `XAG_USD` missing without imputation until a different free provider or symbol is explicitly selected.
- 진행 중:
  - Merge feature branch to `develop`, push, deploy to EC2, and run live route smoke.
- 막힌 점:
  - none currently.

## Exact Next Step

- exact next step: run final local verification, update this handoff with evidence, commit the feature branch, merge to `develop`, push, deploy to EC2, and smoke `/api/market-map` plus `/market-map`.

## Verification

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cross_asset_market tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_frontend_fixture_server`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task cross-asset-provider-quality-and-market-map-v1`
- passed after EC2 smoke fix: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_frontend_fixture_server tests.test_cross_asset_market`
- passed after EC2 smoke fix: `cd apps/web && npm run typecheck && npm run build`
- passed after XAG policy wording update: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cross_asset_market tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_frontend_fixture_server`
- passed after XAG policy wording update: `cd apps/web && npm run typecheck && npm run build`

## EC2 Evidence

- deployed commit before XAG wording update: `eb47ba62`.
- provider smoke: `cross-asset-indicator-provider-fetch-run --as-of-date 2026-06-05 --max-requests-per-run 20 --execute` returned `status=completed_with_failures`, `run_id=3576`, `failed_indicator_count=1`, failed indicator `XAG_USD`, error `HTTP Error 404` after candidates `XAG/USD`, `XAGUSD`, `SILVER`.
- snapshot smoke: `cross-asset-regime-snapshot-run --as-of-date 2026-06-05 --execute` returned `status=completed`, `run_id=3577`, `snapshot_count=39`, `regime_count=10`.
- `/api/market-map?asOfDate=2026-06-05` returned `indicator_count=39`, `fresh_indicator_count=37`, `missing_indicator_count=1`, `stale_indicator_count=1`, quality flags `XAG_USD missing_indicator` and `USD_BROAD_INDEX stale_fred_dollar_index`, `order_boundary=read_only_no_order`, `recommendation_scoring_mutated=false`.
- `http://127.0.0.1:13000/market-map` returned HTTP `200`.

## Guardrails

- Do not change recommendation weights.
- Do not add paid providers.
- Do not expose provider API keys or raw bulk feed dumps.
- Do not add write/order endpoints.
