# Roles

- coordinator/integrator: owns the contract, final semantic decisions, source integration, verification, and commit boundary.
- backend semantics specialist: audits v1 source lineage, horizon/sample behavior, and proposes fail-closed v2 fields.
- product/risk specialist: checks the latest pilot decision, approval requirements, observation-unit risks, and prohibited scope.
- test specialist: defines adversarial TDD, compatibility, append-only SQL, CLI, and data-health regression cases.
- history specialist: preserves legacy terminology and identifies stale/future/source-coherence risks without rewriting past artifacts.
- final reviewers: independently review deterministic semantics, source consistency, and mutation boundaries after implementation.

All specialists are read-only unless the coordinator explicitly assigns non-overlapping implementation ownership. The coordinator alone stages and commits.
