# fred-dollar-index-lag-policy-v1 Handoff

## Status

- current status: completed; implemented, deployed to EC2, and smoke verified.

## Current Status

- 완료:
  - Confirmed on EC2 that `DTWEXBGS` refresh succeeds and FRED's latest official observation is `2026-05-29`.
  - Confirmed the stale flag is caused by official data lag rather than local ingest failure.
  - Updated `USD_BROAD_INDEX` freshness SLA to 10 days with policy `fred_lag_tolerant_no_imputation_weaken_dollar_regime_after_sla`.
  - Added API/UI wording that FRED official publication lag is tolerated, latest observation date is shown, and no imputation is used.
  - Deployed `develop` commit `2af44e93` to EC2.
  - EC2 `macro-batch-upsert --series-id DTWEXBGS` succeeded with `run_id=3656`, latest official observation `2026-05-29`.
  - EC2 `free-provider-capacity-registry-run --execute` succeeded with `run_id=3659`.
  - EC2 `cross-asset-indicator-ingest-run --as-of-date 2026-06-05 --execute` succeeded with `run_id=3660`.
  - EC2 `cross-asset-regime-snapshot-run --as-of-date 2026-06-05 --execute` succeeded with `run_id=3661`.
  - `/api/market-map?asOfDate=2026-06-05` returned `summary.status=available`, `fresh_indicator_count=39`, `stale_indicator_count=0`, `missing_indicator_count=0`, `quality_flags=[]`.
  - `USD_BROAD_INDEX` returned `freshness_status=fresh`, `latest_observation_date=2026-05-29`, `quality_policy=fred_dollar_index_lag_tolerant_no_imputation`.
  - `http://127.0.0.1:13000/market-map` and `/data-health` returned HTTP 200.
- 진행 중:
  - none.
- 막힌 점:
  - none currently.

## Exact Next Step

- exact next step: continue with market-map UX/data interpretation improvements if needed; current FRED dollar lag policy is closed.

## Verification

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cross_asset_market tests.test_frontend_live_adapter`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task fred-dollar-index-lag-policy-v1`

## Guardrails

- Do not impute delayed FRED observations.
- Do not remove the latest observation date from the UI/API.
- Do not change recommendation scoring or broker/order boundaries.
