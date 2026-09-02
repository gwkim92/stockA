# recommendation-weight-review-prospective-evidence-live-observation-v1 Topology

```text
PostgreSQL target
  └─ identity query
       ├─ mismatch / missing relations
       │    └─ blocked, zero domain reads, zero writes
       └─ attested target
            └─ exact lineage ID + exact feedback-calibration ID
                 └─ prospective evidence bundle #1
                      └─ foundation + legacy surface SHA-256
                           └─ dry-run: return, zero writes
                           └─ execute: create ops.pipeline_run
                                └─ exact bundle #2
                                     ├─ surface changed
                                     │    └─ mark pipeline failed; no eval artifact
                                     └─ surface unchanged
                                          └─ append one ai.eval_run observation
                                               └─ mark pipeline succeeded
```

No recommendation, component, outcome, portfolio, rebalance, order, broker, scheduler, deployment, or schema mutation is connected to this topology.
