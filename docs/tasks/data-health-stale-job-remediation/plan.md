# Data Health Stale Job Remediation Plan

## Steps

1. Capture current live `/api/data-health` problem runs without exposing secrets.
2. Run `portfolio-position-daily` through `stockanalysis-operations run` with the repo-outside local positions fixture.
3. Run `portfolio-remediation-daily` through `stockanalysis-operations run` with the same local portfolio scope.
4. Try `performance-outcome-monthly` through the same artifact runner and capture success or root cause.
5. Re-query `/api/data-health` and record remaining attention items.
6. Update handoff/review and run harness/diff verification.

## Non-Goals

- Host scheduler activation
- New shell orchestration scripts
- Provider key changes
- Recommendation/scoring/benchmark changes
- Trading or broker integration
