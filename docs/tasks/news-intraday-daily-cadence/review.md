# Review: news-intraday-daily-cadence

## Result

- EC2 deployment complete.
- `news-intraday` now runs every two hours every day instead of Monday-Friday market-hours only.
- Installed systemd calendar:
  - `OnCalendar=*-*-* 00,02,04,06,08,10,12,14,16,18,20,22:00 America/New_York`
- EC2 next scheduled run:
  - `Sat 2026-05-23 10:00:00 UTC`

## Checks

- Local scheduler unit tests passed.
- Local scheduler invocation verification script passed.
- Local compileall passed.
- Local AWH task verify passed.
- EC2 scheduler unit tests and verification script passed.
- EC2 `systemd-analyze verify` passed for regenerated manifests.
- EC2 `stockanalysis-operating-data-news-intraday.timer` is active and waiting.
- EC2 scheduler status report shows `installed`, `active_timer_count=7`, `timer_count=7`.
- EC2 immediate Persistent run completed with `failed_step_count=0`; RSS translation coverage is `241/241`, pending `0`.

## Risks

- `news-intraday` still bundles RSS fetch, enrichment, Korean translation, cluster evidence, AI candidate extraction, and macro propagation. The two-hour schedule is a practical compromise, but the cleaner long-term split is separate low-cost RSS fetch/enrichment and less frequent Codex OAuth AI extraction profiles.
- Installing a more frequent timer with `Persistent=true` immediately triggered one catch-up run. This was expected and succeeded, but future schedule changes should account for catch-up execution.
