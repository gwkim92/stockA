# analysis-integrity-ci-v1 Plan

## Status

- state: implementation complete; integration tracked in PR `#22`
- base branch: `develop`
- base commit: `229758bbf92ac9843b1aa55e5c96a91868c9513b`
- work branch: `codex/ci-fast-integrity-v1`

## Completed Steps

1. A narrow, non-deploying CI contract was frozen.
2. `scripts/verify_analysis_integrity_ci.sh` was added for the analysis lineage/readiness boundary.
3. `.github/workflows/analysis-integrity.yml` was added with read-only permissions and bounded path filters.
4. Shell syntax, workflow YAML, package metadata, compile, and focused tests were validated.
5. PR `#22` triggered the first `Analysis Integrity` GitHub Actions run.
6. The clean-runner package install and verifier step completed successfully.
7. Review, QA, and handoff evidence were recorded.
8. Manual integration requires the final PR head to remain mergeable with a green `Analysis Integrity` check.

## Deferred Expansion

- complete Python regression discovery
- Docker/PostgreSQL integration checks
- Next.js typecheck/build
- browser and API runtime smoke
- scheduler and host checks

Each expansion remains a separate bounded job or workflow and must first be deterministic on a clean runner.
