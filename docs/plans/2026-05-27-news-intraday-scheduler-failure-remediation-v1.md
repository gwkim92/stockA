# news-intraday-scheduler-failure-remediation-v1 Plan

## Summary

The system is close to an operating MVP, but EC2 `news-intraday` is failing. Since news collection, enrichment, translation, AI extraction, event propagation, and data-health freshness are central to the project goal, this task fixes the automatic short-cycle news path before adding more analysis layers.

## Implementation Order

1. Inspect EC2 systemd unit, timer, and journal logs for `stockanalysis-operating-data-news-intraday.service`.
2. Reproduce the failing command directly with the same env file if safe.
3. Identify whether the failure comes from provider budget/rate limit, RSS ingest, translation, Codex OAuth, DB schema, CLI profile composition, or timeout.
4. Implement the smallest backend-boundary fix.
5. Run the affected local tests and EC2 rerun smoke.
6. Confirm `/api/data-health` and `/data-health` show an explained healthy state or a durable safe skip state.

## Guardrails

- No scoring weight changes.
- No broker/order enablement.
- No paid provider requirement.
- No UI-only hiding of operational failure.
