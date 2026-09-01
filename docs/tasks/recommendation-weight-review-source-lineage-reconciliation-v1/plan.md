# recommendation-weight-review-source-lineage-reconciliation-v1 Plan

## Status

- state: in progress
- base branch: `develop`
- base commit: `366abe812d20fbe059ad5a5b62c501c0107ee9ae`
- work branch: `codex/recommendation-weight-review-source-lineage-reconciliation-v1`

## Steps

1. Freeze the readiness-anchored source-selection and fail-closed contract.
2. Implement one atomic read bundle for readiness, exact referenced quality/outcome, and latest drift observations.
3. Implement a pure reconciliation builder with source identity, date, status, cohort-filter, nested-quality, and canonical-hash validation.
4. Add a narrow executable module and append-only execute path.
5. Add adversarial unit tests for independent-latest drift, missing references, wrong source identity, future dates, filter mismatch, nested-quality mismatch, and permission escalation attempts.
6. Add a repository verifier and operator documentation.
7. Update roadmap and task handoff/review/QA after verification.
8. Push each coherent commit, open a pull request to `develop`, inspect the diff, and merge only after the available checks are green.

## Non-Goals

- rerunning or rewriting readiness, quality, or outcome artifacts
- adding prospective row-level cohort identity
- adding feedback deduplication or a freshness policy
- defining an authoritative horizon or pilot policy
- starting a manual weight-review pilot
- changing any recommendation component weight
- changing portfolio positions, orders, broker integration, scheduler, or deployment
