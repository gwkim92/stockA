# professional-source-gap-prioritization-v1 Plan

## Summary

Outcome windows are currently not due, so the next value is to improve professional analysis trust by making remaining source gaps prioritized and actionable. This keeps the project moving toward analyst-grade company/fund coverage without changing recommendation weights.

## Status

- local implementation complete: `/api/data-health` exposes `professional_source_gap_prioritization`, and `/data-health` renders the ranked source gap list in Korean.
- EC2 deployment/smoke remains the next operational proof.

## Implementation Order

1. Done: inspect professional coverage/source blocker data already returned by backend APIs.
2. Done: add a source-gap prioritization payload using active recommendation exposure and missing layer count.
3. Done: surface the ranked gaps in `/data-health`.
4. Done: add tests for company source blockers, fund not-applicable cases, and remediation actions.
5. Pending: smoke on EC2 without mutating weights or order state.

## Guardrails

- No recommendation weight changes.
- No synthetic financial data.
- No paid provider requirement.
- No broker/order submit.
