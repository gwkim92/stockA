# Market Data Provider Adapter Pilot

## Summary

- Add provider-neutral market price ingest support.
- Keep Alpha Vantage as default.
- Add Twelve Data as the first free broad-market pilot.
- Verify via fixture only in this slice; live API smoke needs a key and explicit approval.

## Implementation

1. Runtime config: `STOCKANALYSIS_TWELVE_DATA_API_KEY`.
2. Source adapter: `twelve_data` with `time_series_daily`.
3. Market price loader: provider-aware payload fetch and normalization.
4. CLI: `--provider alpha_vantage|twelve_data`.
5. Operations runner: provider-specific budget ledger and batch call.
6. Frontend live adapter: data-health provider budget reads `STOCKANALYSIS_MARKET_PRICE_PROVIDER`.
7. Tests: request builder, normalization, upsert config metadata, batch provider propagation, operations runner propagation, and data-health provider-budget selection.

## Guardrails

- No secret output.
- No live call unless separately approved.
- No schema or scoring changes.
