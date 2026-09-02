# recommendation-weight-review-prospective-evidence-foundation-v1 Topology

```text
reconciled source-lineage eval
  ├─ exact quality eval + cohort cutoff
  ├─ exact outcome eval + cohort filters/horizons
  └─ recommendation rows
       ├─ deterministic row identity
       ├─ sorted component snapshot
       └─ linked outcome observations

portfolio feedback calibration
  └─ exact latest_feedback_runs eval IDs
       └─ feedback observation identities
            ├─ duplicate groups
            └─ deduplicated evidence set

all source dates
  └─ versioned conservative freshness evaluation

atomic read bundle
  ► pure read-only foundation artifact
  ► optional append-only ai.eval_run + ops.pipeline_run lifecycle
```

No scoring, weight, portfolio, rebalance, order, broker, scheduler, deployment, or schema mutation is connected to this topology.
