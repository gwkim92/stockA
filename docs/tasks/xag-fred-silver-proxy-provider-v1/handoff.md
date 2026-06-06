# xag-fred-silver-proxy-provider-v1 Handoff

## Status

- current status: implemented locally; develop merge and EC2 smoke pending.

## Current Status

- 완료:
  - Confirmed on EC2 that Twelve Data candidates `XAG/USD`, `XAGUSD`, and `SILVER` all return 404.
  - Confirmed Stooq CSV path requires API key/captcha and is not suitable for unattended scheduler use.
  - Confirmed FRED search returns current daily silver proxy `NASDAQQSLVO`.
  - Updated `XAG_USD` default registry to FRED `NASDAQQSLVO` proxy semantics.
  - Added snapshot/API wording that the series is a silver proxy, not spot XAG/USD.
  - Added regression tests for the provider definition and frontend SQL wording.
- 진행 중:
  - Merge to `develop`, deploy to EC2, run registry/FRED ingest/snapshot smoke, and verify `/market-map`.
- 막힌 점:
  - none currently.

## Exact Next Step

- exact next step: run final local verification, commit feature branch, merge to `develop`, deploy to EC2, then execute registry, FRED ingest, and snapshot smoke for `2026-06-05`.

## Verification

- passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cross_asset_market tests.test_frontend_live_adapter`

## Guardrails

- Do not change recommendation weights.
- Do not add paid providers or captcha/manual provider requirements.
- Do not represent `NASDAQQSLVO` as spot XAG/USD.
- Keep broker/order boundary as `read_only_no_order`.
