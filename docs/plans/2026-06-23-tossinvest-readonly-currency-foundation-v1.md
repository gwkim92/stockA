# TossInvest Readonly Currency Foundation V1 Plan

## Implementation Steps

1. Add nullable DB support for FX snapshots and native currency position values.
2. Add KR market/exchange seed rows.
3. Add TossInvest request builders and RuntimeConfig env keys.
4. Add a read-only sync runner with fixture-backed deterministic mode and live mode that obtains one OAuth token per run.
5. Upsert a separate KRW Toss portfolio, FX evidence, instruments, and converted position snapshots.
6. Add a disabled Toss order adapter stub.
7. Extend frontend coverage, trading readiness, and data-health read models.
8. Add focused tests and verification script.

## Constraints

- Default portfolio: `Toss Real Readonly`.
- Default base currency: `KRW`.
- Env keys:
  - `STOCKANALYSIS_TOSSINVEST_CLIENT_ID`
  - `STOCKANALYSIS_TOSSINVEST_CLIENT_SECRET`
  - optional `STOCKANALYSIS_TOSSINVEST_ACCOUNT_SEQ`
- No repo-inside env files.
- No live order mutation path.

## Done Criteria

- Toss read-only dry-run and fixture-backed execute produce secret-free reports.
- Mixed KRW/USD holdings store base KRW and native values.
- Existing USD paper portfolio SQL remains compatible.
- Frontend APIs expose Toss sync/readiness/currency visibility.
- Full relevant verification is run and residual risks are documented.
