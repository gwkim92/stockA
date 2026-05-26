# source-blocked-recommendation-guardrail-v1 Plan

## Summary

The AI/news quality audit is now green, but professional source gaps still affect user trust. The next highest-risk issue is active recommendations for instruments with durable financial source blockers, especially EROK.

## Implementation Order

1. Inspect `/api/data-health`, `/stocks/EROK`, and the linked EROK recommendation detail payload.
2. Find the deterministic boundary where professional source blocker status should block recommendation professional use.
3. Add a guardrail field/status without changing score weights or deleting historical recommendations.
4. Add focused tests for source-blocked recommendations.
5. Deploy to EC2 and verify EROK recommendation visibility and broker/order boundary.

## Guardrails

- No recommendation weight changes.
- No broker/order enablement.
- No fabricated financial facts.
- No silent deletion of historical recommendation records.
