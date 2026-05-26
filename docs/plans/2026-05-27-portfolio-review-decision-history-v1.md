# portfolio-review-decision-history-v1 Plan

## Summary

Benchmark drift outliers now produce explicit read-only decisions, but the decision state is derived at request time. The next step is to make professional portfolio review decisions auditable over time without changing weights or enabling orders.

## Implementation Order

1. Inspect existing `eval_run`, `ops.pipeline_run`, portfolio risk budget, and paper validation persistence boundaries.
2. Choose the smallest durable storage mechanism for portfolio review decision history.
3. Persist source evidence, decision label, next review action, related thesis/recommendation references, and order boundary.
4. Expose latest/recent review decisions on data-health and portfolio coverage.
5. Add tests, AWH verification, and EC2 smoke.

## Guardrails

- No recommendation weight changes.
- No automatic rebalance or broker submit.
- No benchmark definition changes.
- No portfolio position mutation.
