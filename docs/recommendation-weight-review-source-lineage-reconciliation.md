# Recommendation Weight Review Source Lineage Reconciliation

## Purpose

`recommendation-weight-review-source-lineage-reconciliation-v1` resolves one canonical evidence chain for recommendation-weight review:

```text
readiness audit
  -> exact quality eval referenced by source_eval_run_id
  -> exact outcome eval referenced by outcome_calibration_gate.eval_run_id
```

It does not select the newest quality and outcome rows independently and then pretend that they belong to the selected readiness audit. Newer rows are retained only as drift observations.

## Why This Exists

The readiness-semantics v2 shadow correctly failed closed when readiness `28` referenced quality `26` and outcome `27`, while independent latest selection returned quality `801` and outcome `692`. That result identified a source-selection ambiguity rather than a reason to rewrite historical artifacts.

This task makes the selection rule explicit and reproducible:

1. readiness is the anchor;
2. readiness references are canonical;
3. latest quality/outcome rows are diagnostic only;
4. cohort filters and nested quality content are versioned and hashed;
5. missing or inconsistent evidence fails closed.

## Contracts

Artifact identity:

- eval: `recommendation_weight_review_source_lineage_reconciliation_v1`
- dataset: `recommendation-weight-review-source-lineage-reconciliation-v1`
- source-lineage contract: `recommendation-weight-review-source-lineage-v1`
- cohort-filter contract: `recommendation-weight-review-cohort-filter-v1`
- nested-quality contract: `recommendation-weight-review-nested-quality-v1`

Possible statuses:

- `reconciled_read_only`
- `lineage_incomplete_fail_closed`
- `lineage_incoherent_fail_closed`

A reconciled lineage means only that the historical evidence chain is internally identifiable. It does not mean that the evidence is fresh, statistically sufficient, eligible for a pilot, approved by the user, or allowed to mutate recommendation weights.

## Read Boundary

One atomic PostgreSQL statement returns:

- selected readiness anchor;
- exact referenced quality eval;
- exact referenced outcome eval;
- latest valid quality observation;
- latest valid outcome observation.

The canonical-chain hash excludes latest observations. Therefore a newer quality or outcome run can create a drift diagnostic without silently changing historical lineage identity.

## Integrity Checks

The builder validates:

- source eval names and dataset versions;
- positive eval IDs and exact readiness references;
- created/score dates against the requested as-of date;
- readiness, quality, outcome, and sample statuses;
- required cohort filters: market, strategy, horizon type, universe version;
- top-level versus nested outcome filter equality;
- exact canonical hash equality between referenced quality and outcome-embedded quality.

## Mutation Boundary

Dry-run performs one read and no write.

`--execute` writes only:

- one `ops.pipeline_run` lifecycle;
- one append-only `ai.eval_run` reconciliation artifact.

The result always keeps these states false:

- manual review eligibility;
- pilot scope and pilot start;
- explicit user approval;
- proposal generation;
- recommendation scoring or weight mutation;
- portfolio position mutation;
- automatic order and broker submission.

The order boundary remains `read_only_no_order`.

## Usage

Module CLI:

```bash
PYTHONPATH=src python3 -m \
  stockanalysis.operations.recommendation_weight_review_source_lineage_reconciliation_cli \
  --as-of-date 2026-07-11 \
  --readiness-eval-run-id 28
```

Append-only execution:

```bash
PYTHONPATH=src python3 -m \
  stockanalysis.operations.recommendation_weight_review_source_lineage_reconciliation_cli \
  --as-of-date 2026-07-11 \
  --readiness-eval-run-id 28 \
  --execute
```

Installed entry point:

```bash
stockanalysis-weight-lineage-reconciliation \
  --as-of-date 2026-07-11 \
  --readiness-eval-run-id 28
```

Verification:

```bash
bash scripts/verify_recommendation_weight_review_source_lineage_reconciliation_v1.sh
```

## Next Boundary

After a lineage is reconciled, the next work is prospective rather than historical rewriting:

- stable row-level recommendation cohort identity;
- versioned component snapshots;
- portfolio-feedback deduplication;
- an explicit source-freshness policy;
- a separately reviewed horizon and pilot policy.
