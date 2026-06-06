# fred-dollar-index-lag-policy-v1 Handoff

## Status

- current status: in progress.

## Current Status

- 완료:
  - Confirmed on EC2 that `DTWEXBGS` refresh succeeds and FRED's latest official observation is `2026-05-29`.
  - Confirmed the stale flag is caused by official data lag rather than local ingest failure.
- 진행 중:
  - Add lag-tolerant SLA/policy wording and verify API/UI behavior.
- 막힌 점:
  - none currently.

## Exact Next Step

- exact next step: patch registry definition and frontend wording, run tests, deploy to EC2, and smoke `/api/market-map`.

## Guardrails

- Do not impute delayed FRED observations.
- Do not remove the latest observation date from the UI/API.
- Do not change recommendation scoring or broker/order boundaries.
