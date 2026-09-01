# recommendation-weight-review-source-lineage-reconciliation-v1 Topology

```text
selected readiness audit (anchor)
  ├─ source_eval_run_id ───────────────► exact quality eval
  ├─ outcome_calibration_gate.eval_run_id ► exact outcome eval
  │                                           ├─ cohort filters
  │                                           └─ nested quality score
  └─ canonical readiness-referenced chain

latest quality/outcome as-of observations
  └─ drift diagnostics only; never canonical replacements

atomic read bundle
  ► pure reconciliation builder
  ► dry-run JSON
  ► optional append-only ai.eval_run + ops.pipeline_run lifecycle
```

No scoring, weight, portfolio, order, broker, scheduler, or deployment mutation is connected to this topology.
