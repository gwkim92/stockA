# Market Price Latest Completed Day Policy Plan

## Steps

1. Add pure date policy helpers for latest completed US market day.
2. Wire the policy into `run_market_price_daily_from_env` while preserving explicit overrides.
3. Update CLI help, cadence/runbook docs, and tests.
4. Run focused unit tests.
5. Run a scheduler-free local smoke to confirm fresh 2026-05-18 data skips provider calls.
6. Update handoff/review and run AWH/diff verification.

## Non-Goals

- External holiday calendar integration
- Host scheduler activation
- Provider/account changes
- Scoring, portfolio, benchmark, or trading changes
