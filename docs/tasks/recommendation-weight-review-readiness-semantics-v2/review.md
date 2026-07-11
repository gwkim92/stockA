# recommendation-weight-review-readiness-semantics-v2 Review

## Status

- backend final review: PASS.
- safety final re-review: PASS after deriving integrity from projected fields, requiring loaded/exact portfolio scope, and hard-fixing unimplemented v2 attestations false.

## Initial Findings and Resolution

- future readiness score: readiness v1 has no mandatory `as_of_date`, so the selector accepts a missing score date for compatibility but rejects a future score date when present; `created_at` remains bounded.
- missing/invalid counts: quality recommendation/outcome/positive counts and portfolio feedback run/decision/mature counts are required and relationship-checked.
- horizon integrity: every row must partition its recommendation cohort; summary shape must equal recommendation count × declared horizon count; price fields and column aggregates are required.
- cohort mismatch: top-level and nested market/strategy/horizon/universe filters must match.
- portfolio scope: SQL selection and the pure builder both require `Long Term Paper`.
- stale-policy ambiguity: no arbitrary maximum age is invented. Source ages are recorded, while the absence of an approved freshness policy is an explicit eligibility blocker.
- threshold/eligibility conflation: threshold evidence may be ready, but manual eligibility requires stable identity, feedback deduplication, versioned component snapshots, approved horizon policy, and approved freshness policy. Those attestations are false in v2.
- nested DTO leakage: raw nested objects and `**raw` merges were replaced with exact allowlist projectors and fixed blocked authorization/pilot/mutation objects. Manual eligibility is recomputed from loaded state, exact portfolio scope, and projected individual attestations.

## Boundary Review

- no schema migration.
- no recommendation scoring, weight, benchmark, evaluation-split, portfolio, paper-order, or broker mutation.
- dry-run performs four bounded reads; execute owns only `ops.pipeline_run` lifecycle writes plus one new append-only `ai.eval_run` insert.
- CLI exposes source selectors and execute/dry-run only; it has no approve, authorize, pilot, delta, component-weight, order, or broker argument.
- the new data-health sibling is not consumed by v1 readiness, outcome router, open-gate, scoring, portfolio, or order decisions.

## Remaining Review Risks

- row-level cohort identity, feedback deduplication, component versioning, approved horizon policy, and approved freshness policy are intentionally not implemented; they block eligibility.
- local DB and EC2 artifacts were not generated, so source-shape comparison against live history remains a deployment-stage check.
- the full Python discovery has five unrelated existing env-readiness failures; focused and adjacent task regressions pass.
