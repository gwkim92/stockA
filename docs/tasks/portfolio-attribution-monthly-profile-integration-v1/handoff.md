# portfolio-attribution-monthly-profile-integration-v1 Handoff

## Status

- in progress: root cause identified; implementation pending.

## Context

- `portfolio-attribution-monthly` already exists in the cadence registry.
- `performance-monthly` currently runs only `performance-outcome-monthly`, so the expected attribution job can remain missing forever.
- EC2 evidence before implementation: `performance.attribution_run` count is `0`; `portfolio.position_snapshot` and `performance.thesis_outcome` rows exist.

## Exact Next Step

- exact next step: implement `stockanalysis-operations portfolio-attribution-run`, wire it into `performance-monthly`, and verify locally before EC2 smoke.

