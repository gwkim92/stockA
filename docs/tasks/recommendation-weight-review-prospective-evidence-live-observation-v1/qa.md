# recommendation-weight-review-prospective-evidence-live-observation-v1 QA

## Focused Coverage

The focused suite contains 13 tests covering:

- stable database fingerprint despite JSON relation-key ordering;
- missing relation and wrong fingerprint short-circuit before domain reads;
- same-command target guard on exact bundle reads;
- target predicates on every allowed write statement;
- exact lineage and feedback-calibration IDs in SQL;
- recommendation score and recommended-weight drift changing the legacy hash;
- dry-run zero-write boundary;
- execute destination restriction to `ops.pipeline_run` and `ai.eval_run`;
- concurrent source drift marking the pipeline failed and preventing eval insertion;
- append-only eval SQL excluding portfolio, order, broker, and credential surfaces;
- invalid IDs, environment labels, and SHA-256 values failing before executor use;
- CLI help exposing no approval, pilot, weight, rebalance, order, broker, deployment, or migration flag.

## Required Commands

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_recommendation_weight_review_prospective_evidence_live_observation -v
bash scripts/verify_recommendation_weight_review_prospective_evidence_live_observation_v1.sh
bash scripts/verify_analysis_integrity_ci.sh
git diff --exit-code -- db/migrations
git diff --check
```

## Code-Head Evidence

```text
head: f61854ddeb148686cf743ef98c8d739193ea854b
workflow: Analysis Integrity
run: 33607891527
status: completed
conclusion: success
```
