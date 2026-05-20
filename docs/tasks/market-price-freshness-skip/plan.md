# Market Price Freshness Skip Plan

## Steps

1. Add a latest-price-date lookup helper in the market price ingest module.
2. Add `skip_if_fresh` and `freshness_date` parameters to batch upsert before fixture/provider payload loading.
3. Propagate freshness options through universe backfill, ingest CLI, operations free-backfill runner, and operations CLI.
4. Add unit tests proving fresh symbols are skipped before provider loading and do not consume request budget.
5. Update handoff/review and run focused verification.

## Non-Goals

- Trading calendar/holiday inference
- Automatic scheduler activation
- Broad provider calls
- Schema changes
