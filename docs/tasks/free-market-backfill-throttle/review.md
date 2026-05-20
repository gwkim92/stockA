# Review Notes

- Implemented provider request throttling and request-budget skipping in `run_market_price_batch_upsert`.
- Threaded the same controls through universe backfill and CLI commands.
- Updated `market-price-daily` cadence metadata so the reference command is free-tier safe by default.
- Verified with unit tests and a real Alpha Vantage free daily smoke capped at one provider request.

## Remaining Risks

- Alpha Vantage free `TIME_SERIES_DAILY` remains unadjusted; downstream performance and thesis quality must preserve `price_adjustment_mode=unadjusted_fallback`.
- The daily free limit is enforced by the provider account, not by local persistent state. This slice caps each run, but it does not yet persist a cross-run daily budget ledger.
- Larger universe backfills should wait until a persisted queue/budget runner exists.
