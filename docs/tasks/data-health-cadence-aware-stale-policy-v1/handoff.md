# data-health-cadence-aware-stale-policy-v1 Handoff

## Current Status

- status: in_progress
- started_at: 2026-06-01
- current status: root cause confirmed; implementation pending.
- in progress: data-health SQL needs a daily latest-due calculation before EC2 deploy.

## Root Cause

- EC2 time during investigation was Monday 2026-06-01 02:20 EDT.
- Daily post-market jobs are scheduled Mon-Fri around 18:30-19:50 America/New_York.
- Their latest successful run was Friday 2026-05-29 after the scheduled post-market window.
- Existing data-health SQL used `run.ended_at < now() - stale_after_hours`, so Friday evening runs were marked stale after 36 hours even though Monday's due time had not arrived.
- First EC2 smoke also showed that several `decision-daily` child jobs finish before their display `expected_after_local` values because one profile starts around 19:00 and executes multiple steps in order. Therefore the stale policy must compare the latest due local date, not require completion after each display timestamp.

## Decisions

- Treat daily jobs as due only after the latest Mon-Fri scheduled local date has passed.
- For Monday before the expected local time, the latest due date is the previous Friday.
- For Saturday/Sunday, the latest due date is Friday.
- For Tuesday-Friday before the expected local time, the latest due date is the previous weekday.
- Intraday, weekly, and monthly jobs keep the current stale window behavior in this task.

## Verification Log

- Pending.

## Next Step

- exact next step: verify the revised local-date comparison locally, redeploy it to EC2, and confirm `data_operations_artifact_runner` no longer opens from not-yet-due Friday daily jobs.
