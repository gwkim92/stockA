# professional-source-gap-prioritization-v1 Plan

## Summary

Outcome windows are currently not due, so the next value is to improve professional analysis trust by making remaining source gaps prioritized and actionable. This keeps the project moving toward analyst-grade company/fund coverage without changing recommendation weights.

## Implementation Order

1. Inspect professional coverage/source blocker data already returned by backend APIs.
2. Add a source-gap prioritization payload using active recommendation exposure and missing layer count.
3. Surface the ranked gaps in `/data-health` or the most relevant professional analysis page.
4. Add tests for company source blockers, fund not-applicable cases, and remediation actions.
5. Smoke on EC2 without mutating weights or order state.

## Guardrails

- No recommendation weight changes.
- No synthetic financial data.
- No paid provider requirement.
- No broker/order submit.
