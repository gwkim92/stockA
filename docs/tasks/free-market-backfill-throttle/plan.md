# Implementation Plan

## Steps

- Extend market price batch upsert with `throttle_seconds`, `max_requests_per_run`, and injectable `sleeper`.
- Return `provider_request_count`, `skipped_symbol_count`, and explicit skipped result rows.
- Thread the new options through universe backfill and CLI parsers.
- Add unit tests for throttle spacing and budget skip behavior.
- Run a small real watchlist smoke with max request budget no greater than 3.

## Safety

- Do not print provider key values.
- Do not exceed the configured request budget.
- Do not activate scheduler or write LaunchAgents.
