# recommendation-weight-review-source-lineage-reconciliation-v1 Review

## Review Decision

- decision: approve for pull request to `develop`
- blocking findings: none in the focused implementation review
- scope reviewed: atomic source lookup, pure reconciliation builder, append-only execute path, CLI, tests, verifier, task/operator documentation

## Findings

### Canonical Source Ownership

- The readiness audit is the only canonical anchor.
- Quality is resolved by the readiness score's exact `source_eval_run_id`.
- Outcome is resolved by the readiness score's exact `outcome_calibration_gate.eval_run_id`.
- Independently selected latest quality/outcome rows are isolated under non-authoritative drift diagnostics.
- The canonical-chain hash excludes latest observations, so later evidence cannot silently rewrite historical lineage identity.

### Fail-Closed Behavior

- Missing anchor, missing reference, or missing referenced artifact yields `lineage_incomplete_fail_closed`.
- Wrong eval identity, reference mismatch, status mismatch, future-dated source, cohort mismatch, or nested-quality mismatch yields `lineage_incoherent_fail_closed`.
- A coherent historical chain yields `reconciled_read_only` only; it does not confer freshness, statistical sufficiency, pilot eligibility, or mutation permission.

### Integrity And Permission Boundary

- Required cohort filters are versioned and hashed.
- The exact referenced quality score and outcome-embedded quality score must have the same canonical hash.
- Adversarial source fields cannot make the output authoritative or enable approval, pilot, proposal, weight, portfolio, order, or broker permissions.
- Dry-run reads once and writes nothing.
- Execute mode writes only one `ops.pipeline_run` lifecycle and one append-only reconciliation `ai.eval_run`.

## Non-Blocking Risks

- A live PostgreSQL execution against the repository's real `ai.eval_run` history was not performed in this environment.
- The full repository regression suite and Docker-backed verification were not executed because the current runtime cannot resolve GitHub for a complete clone.
- The implementation intentionally validates legacy score shapes at runtime rather than migrating or rewriting them.
- Reconciliation does not solve prospective row-level identity, component snapshotting, feedback deduplication, or freshness policy; these remain the next bounded work.

## Merge Conditions

- Branch remains based directly on the current `develop` head with no behind commits.
- Pull-request diff contains no migration, recommendation-scoring, portfolio, broker, scheduler, or deployment changes.
- Available PR checks and mergeability must be inspected before manual merge.
