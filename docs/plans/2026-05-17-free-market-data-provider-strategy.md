# Free Market Data Provider Strategy

## Summary

- Alpha Vantage is not limited to one request per day. Official free-tier guidance says 25 requests/day.
- The one-call limit was our conservative local smoke setting, not the provider limit.
- 25 requests/day is still insufficient for broad universe operations.
- The project needs provider-neutral price ingest and at least one no-cost alternative pilot.

## Provider Ranking

1. Twelve Data pilot first.
   - Reason: free Basic plan documents 800 API credits/day.
   - Fit: enough for incremental watchlist plus moderate universe refresh if cached and throttled.

2. Polygon Stocks Basic second.
   - Reason: official free plan documents 5 API calls/minute, 2 years historical data, EOD data, reference data.
   - Fit: clean API and official market-data provider, but history depth is shorter on free plan.

3. Financial Modeling Prep third.
   - Reason: official free plan documents 250 calls/day.
   - Fit: useful backup if endpoint-level historical price access works under free plan.

4. Stooq as historical CSV fallback.
   - Reason: broad historical CSV availability.
   - Risk: not a clean API-first provider and terms/automation limits need validation.

5. Yahoo/yfinance not primary.
   - Reason: unofficial wrappers are operationally and legally fragile for automated ingestion.

## Implementation Direction

- Add `MarketPriceProvider` adapter interface for daily OHLCV.
- Keep provider output normalized into existing `market.daily_price_bar`.
- Add provider-specific budget ledger keys, not only `alpha_vantage`.
- Keep Alpha Vantage as fallback for priority symbols.
- Add data-health provider comparison: configured, remaining budget, latest successful run, adjusted/unadjusted mode.

## Guardrails

- No hidden scraping as primary source.
- No public redistribution assumption from free providers.
- No provider call in tests unless explicit live smoke.
- Do not change scoring or benchmark until data quality is measured.
