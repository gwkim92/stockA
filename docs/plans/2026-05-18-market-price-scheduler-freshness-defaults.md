# Market Price Scheduler Freshness Defaults Plan

## Summary

Recurring market-price jobs should use the same safe path proven in local MVP: Twelve Data provider, repo-outside watchlist and ledger, freshness skip, and capped requests. This plan updates the scheduler command boundary without activating host scheduler state.

## Key Changes

- Add an operations CLI command that reads market-price watchlist/ledger/provider from env.
- Validate market-price provider readiness through provider-specific key, watchlist CSV, and ledger path.
- Export scheduler run date so the child command can use it as the default freshness date.
- Update cadence/runbook defaults away from Alpha Vantage placeholders.

## Verification

- Focused unit tests.
- Repo-outside env readiness check.
- Scheduler boundary preflight.
- Scheduler boundary local run that should skip all fresh symbols and consume zero provider calls.

## Boundaries

- No `launchctl`.
- No host LaunchAgents writes.
- No secrets in repo or logs.
