# recommendation-weight-review-prospective-evidence-foundation-v1 Review

## Decision

- decision: approve for integration when the final PR head remains mergeable and `Analysis Integrity` is green
- blocking findings: none in the focused implementation review
- reviewed scope: exact source selection, recommendation/component/outcome identity, feedback deduplication, candidate freshness evaluation, runner/CLI, tests, verifier, and CI coverage

## Findings

### Exact Source Ownership

- The foundation starts from one reconciled source-lineage artifact.
- Quality and outcome artifacts are resolved by exact IDs from that lineage.
- Recommendation rows are reconstructed at the exact quality cutoff using the canonical cohort filters.
- Feedback artifacts are resolved only from the selected `Long Term Paper` calibration artifact's `latest_feedback_runs` references.
- Independently selected latest artifacts cannot replace any canonical reference.

### Stable Identity And Snapshot Integrity

- Recommendation identity is independent of input ordering and binds market, strategy, horizon, universe, batch date, instrument, and symbol.
- Database recommendation IDs are retained as source references and must map one-to-one to deterministic identities.
- Component rows are canonicalized and sorted before hashing; missing, duplicate, invalid, or future-dated rows fail closed.
- Outcome observations bind recommendation identity, measurement dates, and horizon, and are checked against reconstructed quality and horizon counts.

### Feedback Deduplication

- Exact repeated observations share one identity and count once.
- Duplicate groups preserve contributing feedback eval IDs.
- The deduplicated manifest excludes rerun IDs, so a newer exact duplicate does not change the evidence-set hash.
- Changed evidence creates a new identity; conflicting payloads under one identity fail closed.

### Freshness And Authorization Boundary

- The conservative freshness policy is explicit, versioned, hashed, and rejection-only.
- Fresh, stale, missing, and future states are represented separately.
- The policy remains unapproved and cannot make evidence eligible.
- Every pilot, proposal, scoring, weight, portfolio, rebalance, order, and broker permission remains hard false.

## Non-Blocking Risks

- The atomic SQL has not been executed against the live PostgreSQL history in this task.
- Candidate max-age limits have not been approved as an authoritative review or pilot policy.
- Complete repository regression, Docker/PostgreSQL integration, frontend build, browser QA, EC2, scheduler, deployment, order, and broker verification remain outside this task.
- No schema-level identity column or uniqueness constraint was added; this task deliberately proves the contract in an append-only audit artifact first.

## Merge Conditions

- PR `#23` final head must be mergeable.
- The `Analysis Integrity` workflow associated with the final head must conclude `success`.
- Diff must contain no migration, recommendation-scoring mutation, portfolio, scheduler, deployment, order, or broker changes.