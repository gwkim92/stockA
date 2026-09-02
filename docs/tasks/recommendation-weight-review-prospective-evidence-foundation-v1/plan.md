# recommendation-weight-review-prospective-evidence-foundation-v1 Plan

## Status

- state: in progress
- base branch: `develop`
- base commit: `ba2b32ce71d15b772e401c72d7a79fb24018a392`
- work branch: `codex/recommendation-weight-review-prospective-evidence-foundation-v1`

## Steps

1. Freeze the source-selection, identity, deduplication, freshness, and mutation-boundary contracts.
2. Implement one atomic read bundle anchored to a reconciled lineage artifact and exact feedback-run references.
3. Implement deterministic recommendation, component, outcome, feedback, cohort, and policy hashes.
4. Validate one-to-one identities, source counts, references, duplicate groups, and dates with fail-closed statuses.
5. Add dry-run and append-only execute modes through a narrow CLI.
6. Add adversarial and ordering-invariance tests plus a repository verifier.
7. Extend the existing Analysis Integrity CI bundle to cover the new module and tests.
8. Push coherent commits, open a PR to `develop`, inspect the real GitHub Actions run, and merge only after the final head is green and mergeable.

## Non-Goals

- no approved horizon policy
- no approved freshness policy
- no pilot parameters or user authorization record
- no recommendation weight proposal or mutation
- no portfolio, order, broker, scheduler, deployment, schema, or API cutover
