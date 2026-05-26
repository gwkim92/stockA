# portfolio-attribution-monthly-profile-integration-v1 Handoff

## Status

- completed: `portfolio-attribution-monthly` now runs through the `stockanalysis-operations` backend CLI boundary and is part of the `performance-monthly` operating-data profile.

## Context

- `portfolio-attribution-monthly` already exists in the cadence registry.
- Root cause before implementation: `performance-monthly` ran only `performance-outcome-monthly`, so the expected attribution job could remain missing forever.
- EC2 evidence before implementation: `performance.attribution_run` count was `0`; `portfolio.position_snapshot` and `performance.thesis_outcome` rows existed.
- Implementation adds `stockanalysis-operations portfolio-attribution-run`, resolves the latest eligible portfolio snapshot/outcome window, and calls the existing deterministic `run_portfolio_attribution_bootstrap` when a window exists.
- If no eligible window exists, the runner records a successful no-op `ops.pipeline_run` with an explicit reason. This avoids false missing-job alerts without fabricating attribution rows.
- `performance-monthly` now plans `performance-outcome-monthly` followed by `portfolio-attribution-monthly`.
- EC2 direct runner smoke on 2026-05-27 selected snapshot `2026-05-22`, measurement end `2026-05-22`, covered `NVDA`, wrote `run_id=1704`, `attribution_run_id=1`, `candidate_count=1`, `component_count=3`, and preserved `order_boundary=read_only_no_order`.
- EC2 `performance-monthly` profile smoke completed with `failed_step_count=0`; the two planned steps were `performance-outcome-monthly` and `portfolio-attribution-monthly`.
- EC2 `/api/data-health` now reports `portfolio-attribution-monthly` as `latest_status=succeeded`, `health_status=ok`, `latest_run_id=pipeline-run-1706`.

## Exact Next Step

- exact next step: address the remaining project-level data-health gates that still keep `overall_status=attention_required`, prioritizing gates that affect professional investment evidence quality over cosmetic UI work.
