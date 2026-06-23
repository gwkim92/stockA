# TossInvest Candle Provider V1 Plan

## Implementation Steps

1. Add `candles` dataset support to `TossInvestSource`.
2. Add daily Toss candle payload normalization into `MarketDailyPriceBarRecord`.
3. Allow `provider=tossinvest` in the existing market price sync path.
4. Add focused tests and a task verification script.
5. Keep production scheduler/provider unchanged until EC2 live Toss access and rate-limit behavior are verified.

## Constraints

- Read-only market data only.
- No live order submit, modify, cancel, or order history mutation.
- No secret values in logs, reports, fixtures, or docs.
- Use `market.daily_price_bar` as the canonical candle table.

## Done Criteria

- Toss candle request builder is covered by tests and redacts authorization.
- Toss daily candle payloads normalize deterministically.
- Existing Alpha Vantage and Twelve Data behavior remains compatible.
- Verification script passes locally.
