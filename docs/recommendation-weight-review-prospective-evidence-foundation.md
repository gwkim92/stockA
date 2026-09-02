# Recommendation Weight Review Prospective Evidence Foundation

## Purpose

`recommendation-weight-review-prospective-evidence-foundation-v1` turns a reconciled historical source chain into a deterministic, read-only evidence snapshot for future recommendation-weight review.

It establishes four missing integrity layers:

1. stable recommendation-row identity;
2. versioned component snapshots;
3. deduplicated portfolio-feedback observations;
4. an explicit, versioned candidate freshness policy.

It does not approve a policy, start a pilot, generate a weight proposal, change recommendation scoring, rebalance a portfolio, create an order, or submit to a broker.

## Source Ownership

The lookup is anchored to one successful `recommendation_weight_review_source_lineage_reconciliation_v1` artifact. Quality and outcome artifacts are resolved only by the exact eval IDs recorded in that lineage.

The portfolio-feedback side selects one `Long Term Paper` calibration artifact and resolves only the exact feedback eval IDs listed in its `latest_feedback_runs` array. Independently selected latest rows cannot replace either chain.

One PostgreSQL statement returns the lineage, exact quality and outcome artifacts, recommendation/component rows, linked outcomes, feedback calibration, and referenced feedback artifacts.

## Identity Contracts

- recommendation row: `recommendation-row-identity-v1`
- component snapshot: `recommendation-component-snapshot-v1`
- outcome observation: `recommendation-outcome-observation-v1`
- feedback deduplication: `portfolio-feedback-deduplication-v1`
- cohort snapshot: `recommendation-cohort-snapshot-v1`

A recommendation identity includes market, strategy, horizon type, universe version, batch date, instrument ID, and normalized primary symbol. The database `recommendation_id` remains a separate source reference and must map one-to-one to the deterministic identity.

Components are canonicalized and sorted by component name before hashing. The component manifest is bound to the recommendation identity, so a component score, weight, explanation, timestamp, or membership change produces a different snapshot hash.

Outcome identity binds the recommendation identity to measurement start date, measurement end date, and horizon. The builder also reconstructs the distinct quality-outcome count and recommendation-by-horizon counts to compare them with the exact source artifacts.

## Feedback Deduplication

Each feedback observation binds:

- source history eval and date;
- decision index, family, type, and symbol;
- related recommendation and thesis references;
- recommendation/thesis outcome references;
- latest price-evidence date;
- paper-validation run reference.

Exact repeats share one observation identity and count once in deduplicated summaries. Duplicate groups retain every contributing feedback eval ID for auditability. A changed evidence reference creates a distinct observation. The same identity with conflicting payloads fails closed.

The deduplicated manifest contains only sorted identity and payload hashes, so adding a newer exact duplicate run does not change the evidence-set hash.

## Candidate Freshness Policy

Policy version: `recommendation-weight-review-conservative-freshness-v1`

- lineage reconciliation: 14 days
- referenced quality: 31 days
- referenced outcome: 31 days
- portfolio-feedback calibration: 31 days
- referenced feedback run: 31 days

Dates are classified as `fresh`, `stale`, `missing`, or `future`. The policy is conservative and rejection-only. It is defined and hashed but not approved, so it cannot make evidence pilot-eligible.

## Result States

- `foundation_complete_fresh_read_only`
- `foundation_complete_stale_read_only`
- `foundation_incomplete_fail_closed`
- `foundation_incoherent_fail_closed`

A complete state attests only that the observed identities, component snapshots, outcomes, references, and deduplicated feedback set are structurally reproducible. Eligibility-level freshness, an approved horizon policy, explicit user authorization, and pilot scope remain unattested.

## Execution Boundary

Dry-run performs one atomic read and no write.

`--execute` writes only:

- one `ops.pipeline_run` lifecycle;
- one append-only foundation row in `ai.eval_run`.

Every approval, pilot, proposal, scoring, weight, portfolio, rebalance, order, and broker permission remains false. The order boundary is always `read_only_no_order`.

## Usage

Preview using the latest valid anchors:

```bash
stockanalysis-weight-prospective-evidence \
  --as-of-date 2026-07-15
```

Preview using exact anchors:

```bash
stockanalysis-weight-prospective-evidence \
  --as-of-date 2026-07-15 \
  --lineage-eval-run-id <lineage-eval-id> \
  --portfolio-feedback-calibration-eval-run-id <feedback-calibration-eval-id>
```

Append the read-only audit artifact:

```bash
stockanalysis-weight-prospective-evidence \
  --as-of-date 2026-07-15 \
  --lineage-eval-run-id <lineage-eval-id> \
  --portfolio-feedback-calibration-eval-run-id <feedback-calibration-eval-id> \
  --execute
```

Verification:

```bash
bash scripts/verify_recommendation_weight_review_prospective_evidence_foundation_v1.sh
bash scripts/verify_analysis_integrity_ci.sh
```

## Next Boundary

The next safe step is an append-only live-database observation using exact source IDs, followed by a separate review of the observed mismatch/staleness results. Approved horizon/freshness policy and any manual pilot packet remain separate tasks.