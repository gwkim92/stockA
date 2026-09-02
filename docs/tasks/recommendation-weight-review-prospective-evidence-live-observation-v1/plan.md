# recommendation-weight-review-prospective-evidence-live-observation-v1 Plan

## Status

- base branch: `develop`
- base commit: `81f1339be2c332068dca679dc741fe50154e139e`
- work branch: `codex/recommendation-weight-review-prospective-evidence-live-observation-v1`

## Steps

1. Freeze exact-source, database-identity, legacy-surface, and write-boundary contracts.
2. Implement identity-first fail-closed preflight.
3. Reuse the merged foundation builder with exact IDs only.
4. Add before/after legacy-surface hashing around the allowed pipeline lifecycle.
5. Insert one append-only observation only after stability is attested.
6. Add adversarial tests, CLI, verifier, package entry point, and CI coverage.
7. Open a PR to `develop`, inspect the final GitHub Actions run, and merge only when green and mergeable.

## Non-Goals

- no live target guessing
- no approved horizon or freshness policy
- no pilot parameters or authorization
- no proposal, scoring, weight, portfolio, order, broker, scheduler, deployment, or schema mutation
