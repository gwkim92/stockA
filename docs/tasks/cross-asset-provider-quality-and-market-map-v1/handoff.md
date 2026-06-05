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

## Guardrails

- Do not change recommendation weights.
- Do not add paid providers.
- Do not expose provider API keys or raw bulk feed dumps.
- Do not add write/order endpoints.
