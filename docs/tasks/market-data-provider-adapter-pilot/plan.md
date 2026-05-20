# Market Data Provider Adapter Pilot Plan

## Steps

1. Add Twelve Data API key runtime config and source registry entry.
2. Implement Twelve Data `time_series_daily` request builder.
3. Extend market price normalization/upsert functions with a provider parameter.
4. Pass provider through ingest CLI, universe backfill, and operations free-backfill runner.
5. Add Twelve Data fixture and unit tests.
6. Update handoff/review and run focused verification.

## Non-Goals

- Live Twelve Data API call
- New DB schema
- Scoring or benchmark changes
- Scheduler activation
- Trading integration
