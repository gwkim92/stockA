# TossInvest Market Data, Agent Context, Paper/Live Split V1

## Summary

Add TossInvest read-only market data as a provider-evidence layer for all tracked symbols, expose candlesticks on stock detail pages, and clearly split paper-trading validation from live Toss read-only account visibility.

## Implementation Notes

- Store TossInvest provider evidence in dedicated market snapshot tables.
- Keep existing canonical daily prices intact while adding provider provenance and comparison evidence.
- Add market-context read models that AI agents can consume without direct TossInvest HTTP access.
- Add operations profiles and cadence metadata for KR/US reference, daily candles, priority microdata, and live account read-only sync.
- Add stock-detail candlestick UI with source/freshness labels and safe empty states.

## Safety

- No TossInvest live order submit, modify, cancel, or mutation endpoint is introduced.
- Secrets stay in repo-outside env files and are not logged or returned in API payloads.
- Live Toss account data is excluded from recommendation/scoring contexts by default.
