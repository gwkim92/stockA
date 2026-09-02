# recommendation-weight-review-prospective-evidence-live-observation-v1 QA

## Focused Coverage

- stable database fingerprint despite JSON relation-key ordering;
- missing relation and wrong fingerprint short-circuit before domain reads;
- exact lineage and feedback-calibration IDs in SQL;
- recommendation score and recommended-weight drift changes the legacy hash;
- dry-run zero-write boundary;
- execute destination restriction to `ops.pipeline_run` and `ai.eval_run`;
- concurrent source drift marks pipeline failed and prevents eval insertion;
- append-only eval SQL excludes recommendation, portfolio, order, broker, and credential surfaces;
- invalid IDs, environment labels, and SHA-256 values fail before executor use;
- CLI help exposes no approval, pilot, weight, rebalance, order, broker, deployment, or migration flag.

## Required Commands

```bash
PYTHONPATH=src python3 -m unittest \
  tests.test_recommendation_weight_review_prospective_evidence_live_observation -v
bash scripts/verify_recommendation_weight_review_prospective_evidence_live_observation_v1.sh
bash scripts/verify_analysis_integrity_ci.sh
git diff --exit-code -- db/migrations
git diff --check
```
