# recommendation-weight-review-prospective-evidence-foundation-v1 Contract

## Task Request

- request: continue the recommendation-weight evidence roadmap after canonical source-lineage reconciliation.
- required foundation: prospective recommendation row identity, versioned component snapshots, portfolio-feedback deduplication, and an explicit source-freshness policy.

## Goal

Add a deterministic, read-only evidence artifact that reconstructs the exact recommendation cohort behind a reconciled readiness → quality → outcome chain, binds each recommendation to an immutable component snapshot, deduplicates repeated portfolio-feedback observations, and evaluates every source against one versioned conservative freshness policy.

The artifact is evidence plumbing only. It cannot authorize a manual pilot, generate a weight proposal, change recommendation scoring, mutate a portfolio, submit an order, or call a broker.

## Canonical Selection Contract

1. Select one successful `recommendation_weight_review_source_lineage_reconciliation_v1` artifact by explicit eval ID or latest valid artifact at the requested audit date.
2. Resolve the exact quality and outcome eval IDs already recorded in that lineage; never substitute independently selected latest artifacts.
3. Reconstruct recommendation rows using the lineage cohort filters and the exact quality score date as the cohort cutoff.
4. Select one `Long Term Paper` portfolio-feedback calibration artifact by explicit eval ID or latest valid artifact at the requested audit date.
5. Resolve only the exact feedback eval IDs listed in that calibration artifact's `latest_feedback_runs` array.
6. Return lineage, exact source evals, recommendation/component rows, outcome rows, feedback calibration, and exact feedback artifacts in one PostgreSQL read statement.

## Identity Contracts

- recommendation row contract: `recommendation-row-identity-v1`
- component snapshot contract: `recommendation-component-snapshot-v1`
- outcome observation contract: `recommendation-outcome-observation-v1`
- feedback deduplication contract: `portfolio-feedback-deduplication-v1`
- cohort snapshot contract: `recommendation-cohort-snapshot-v1`
- freshness policy: `recommendation-weight-review-conservative-freshness-v1`

Recommendation identity is derived from market, strategy, horizon type, universe version, batch date, instrument ID, and primary symbol. The source surrogate `recommendation_id` is preserved separately and must map one-to-one to the deterministic identity.

Component snapshots sort and canonicalize every `(recommendation_id, component_name)` row and bind the resulting SHA-256 to the recommendation identity. Outcome observations bind measurement dates and horizon to the same recommendation identity. Feedback observations bind source history, decision, related recommendation/thesis, and exact evidence references before deduplication.

## Freshness Policy

The policy is fixed and versioned in code. It is conservative and rejection-only:

- lineage reconciliation: 14 days
- referenced quality: 31 days
- referenced outcome: 31 days
- portfolio feedback calibration: 31 days
- referenced feedback run: 31 days

The artifact may report that the candidate policy passes or that stale sources exist. The policy is not an approved pilot policy, so `freshness_policy_approved` and eligibility-level `freshness_policy_attested` remain false.

## Mutable Surface

- `src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_foundation.py`
- `src/stockanalysis/operations/recommendation_weight_review_prospective_evidence_foundation_cli.py`
- `tests/test_recommendation_weight_review_prospective_evidence_foundation.py`
- `scripts/verify_recommendation_weight_review_prospective_evidence_foundation_v1.sh`
- `scripts/verify_analysis_integrity_ci.sh`
- `pyproject.toml` for one narrow entry point
- `.github/workflows/analysis-integrity.yml` only if path coverage requires adjustment
- `docs/recommendation-weight-review-prospective-evidence-foundation.md`
- this task directory and bounded roadmap/handoff documentation

## Invariants

- no migration;
- no update/delete of legacy evals or domain tables;
- dry-run performs one atomic read and no write;
- execute writes only one `ops.pipeline_run` lifecycle and one append-only `ai.eval_run` artifact;
- no independent-latest replacement of lineage references;
- duplicate feedback observations are counted once in deduplicated summaries and are never silently discarded;
- missing/colliding recommendation identities, component rows, outcome references, feedback references, or source dates fail closed;
- recommendation scores, component weights, portfolio positions, benchmark definitions, orders, broker integration, schedulers, deployment, and API decisions remain unchanged;
- every approval, pilot, proposal, mutation, rebalance, order, and broker permission remains hard false.

## Result States

- `foundation_complete_fresh_read_only`
- `foundation_complete_stale_read_only`
- `foundation_incomplete_fail_closed`
- `foundation_incoherent_fail_closed`

A complete result attests only the observed structural identities and deduplicated evidence set. It does not attest an approved horizon policy, approved freshness policy, user authorization, or pilot eligibility.

## Acceptance Criteria

- one atomic SQL statement returns all required sources and rows;
- recommendation deterministic identities are unique and stable under input ordering;
- recommendation IDs and deterministic identities are one-to-one;
- each recommendation has a non-empty, unique-name component snapshot;
- component and cohort hashes change when component content changes;
- outcome observations reference known recommendation identities and have unique deterministic keys;
- exact feedback run references match the calibration artifact;
- exact duplicate feedback observations are identified and counted once;
- a changed evidence reference creates a distinct feedback observation;
- source ages are evaluated against the versioned policy, including missing, future, fresh, and stale states;
- source counts agree with the referenced quality/outcome artifacts;
- dry-run and execute write boundaries are covered by tests;
- focused tests, compile, CLI safety scan, package entry point, migration diff, and GitHub Actions pass.

## Verification Commands

- `PYTHONPATH=src python3 -m unittest tests.test_recommendation_weight_review_prospective_evidence_foundation -v`
- `PYTHONPATH=src python3 -m stockanalysis.operations.recommendation_weight_review_prospective_evidence_foundation_cli --help`
- `bash scripts/verify_recommendation_weight_review_prospective_evidence_foundation_v1.sh`
- `bash scripts/verify_analysis_integrity_ci.sh`
- `git diff --exit-code -- db/migrations`
- `git diff --check`
