# Scheduler Activation Market Price Evidence Plan

## Steps

1. Generate repo-outside operator dry-run evidence for `market-price-daily`.
2. Generate repo-outside pending approval gate evidence from that dry-run report.
3. Update operator dry-run documentation and representative verification scripts to use market-price provider env readiness and `market-price-daily-run --skip-if-fresh`.
4. Re-run targeted scheduler/evidence verification scripts.
5. Update local live MVP handoff/review with the new evidence paths and residual approval boundary.

## Non-Goals

- Host scheduler activation.
- User approval record creation.
- Production deployment.
- Provider network calls.
