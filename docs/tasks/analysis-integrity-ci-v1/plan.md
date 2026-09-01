# analysis-integrity-ci-v1 Plan

## Status

- state: in progress
- base branch: `develop`
- base commit: `229758bbf92ac9843b1aa55e5c96a91868c9513b`
- work branch: `codex/ci-fast-integrity-v1`

## Steps

1. Freeze a narrow, non-deploying CI contract.
2. Add one repository verifier for the analysis lineage/readiness boundary.
3. Add one GitHub Actions workflow with read-only permissions and relevant path filters.
4. Validate shell, YAML, package metadata, compile, and focused tests locally.
5. Open a pull request to `develop` and inspect the actual Actions run.
6. Fix workflow-only issues on the branch, then record review/QA/handoff.
7. Manually merge only when the PR is mergeable and the workflow is green.
