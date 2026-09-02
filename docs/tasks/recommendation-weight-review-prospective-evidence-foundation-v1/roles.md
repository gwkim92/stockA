# recommendation-weight-review-prospective-evidence-foundation-v1 Roles

- planner: owns identity/freshness contracts, invariants, and non-goals.
- implementer: builds the atomic lookup, pure evidence builder, append-only runner, and CLI.
- test owner: covers stable ordering, collisions, missing rows, count mismatch, duplicate feedback, freshness, and permission escalation.
- reviewer: verifies exact source ownership and that deduplication cannot inflate evidence counts.
- operator: may run dry-run or append-only execute; cannot use this artifact to start a pilot or mutate scoring/trading state.
