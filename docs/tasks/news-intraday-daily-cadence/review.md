# Review: news-intraday-daily-cadence

## Result

- Pending EC2 deployment.
- Local scheduler rendering now produces a daily two-hour `news-intraday` systemd calendar instead of a weekday-only market-hours calendar.

## Checks

- Local scheduler unit tests passed.
- Local scheduler invocation verification script passed.
- Local compileall passed.

## Risks

- `news-intraday` still bundles RSS fetch, enrichment, Korean translation, cluster evidence, AI candidate extraction, and macro propagation. The two-hour schedule is a practical compromise, but the cleaner long-term split is separate low-cost RSS fetch/enrichment and less frequent Codex OAuth AI extraction profiles.
