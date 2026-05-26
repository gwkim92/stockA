# benchmark-drift-outlier-decision-v1 Plan

## Summary

The source-blocked recommendation guardrail is now in place. The next remaining high-value gate is benchmark drift: the system has benchmark composition coverage and drift outlier data, but the user still needs clear decisions on what to review.

## Implementation Order

1. Inspect live EC2 benchmark drift, rebalance candidate review, and position sizing payloads.
2. Identify the deterministic boundary where drift outliers should become review decisions.
3. Add read-only decision fields without changing weights, benchmark composition, or orders.
4. Add focused tests and UI visibility.
5. Deploy to EC2 and verify data-health/portfolio coverage routes.

## Guardrails

- No recommendation weight changes.
- No automatic rebalance or broker submit.
- No benchmark definition changes.
- No silent hiding of drift outliers.
