# recommendation-weight-review-prospective-evidence-foundation-v1 Plan

## Status

- state: implementation and focused verification complete; integration tracked in PR `#23`
- base branch: `develop`
- base commit: `ba2b32ce71d15b772e401c72d7a79fb24018a392`
- work branch: `codex/recommendation-weight-review-prospective-evidence-foundation-v1`

## Completed Steps

1. Source-selection, identity, deduplication, freshness, and mutation-boundary contracts were frozen.
2. One atomic read bundle was implemented around a reconciled lineage artifact and exact feedback-run references.
3. Deterministic recommendation, component, outcome, feedback, cohort, and policy hashes were implemented.
4. One-to-one identities, source counts, references, duplicate groups, snapshot fields, canonical hashes, and dates now fail closed when incomplete or inconsistent.
5. One-read dry-run and append-only execute modes were exposed through a narrow CLI.
6. Twenty-five focused tests and a dedicated repository verifier were added.
7. The existing `Analysis Integrity` CI bundle now compiles and tests the new boundary.
8. PR `#23` was opened, temporary connector probe files were removed, and the cleaned implementation head passed GitHub Actions. Final documentation was added; manual merge requires the final head to remain green and mergeable.

## Deferred Work

- append-only live PostgreSQL observation using exact source IDs
- authoritative horizon-policy review
- authoritative freshness-policy review
- scoped pilot parameters and explicit user authorization

## Non-Goals Preserved

- no approved horizon or freshness policy
- no pilot start or proposal generation
- no recommendation score or component-weight mutation
- no portfolio, rebalance, order, broker, scheduler, deployment, schema, or API cutover