# recommendation-weight-review-source-lineage-reconciliation-v1 Roles

- planner: freezes source ownership, invariants, acceptance criteria, and non-goals.
- implementer: adds the atomic read bundle, pure reconciliation builder, append-only runner, and narrow CLI.
- test owner: validates coherent, incomplete, incoherent, drifted, future-dated, and adversarial permission cases.
- reviewer: checks that latest observations never replace readiness references and that all mutation permissions remain false.
- operator: may run dry-run or append-only execute; cannot use this artifact to authorize a pilot, weight change, or order.
