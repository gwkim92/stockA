# recommendation-weight-review-prospective-evidence-live-observation-v1 Topology

```text
PostgreSQL target
  └─ initial identity query
       ├─ mismatch / missing relations
       │    └─ blocked, zero domain reads, zero writes
       └─ attested target identity
            └─ exact lineage ID + exact feedback-calibration ID
                 └─ same-command identity guard + exact bundle #1
                      └─ foundation + legacy surface SHA-256
                           ├─ dry-run: return, zero writes
                           └─ execute
                                └─ guarded ops.pipeline_run insert
                                     └─ same-command identity guard + exact bundle #2
                                          ├─ surface changed
                                          │    └─ guarded failed update; no eval artifact
                                          └─ surface unchanged
                                               └─ guarded ai.eval_run append
                                                    └─ guarded succeeded update
```

Every protected SQL command repeats the observed target identity. No recommendation, component, outcome, portfolio, rebalance, order, broker, scheduler, deployment, or schema mutation is connected to this topology.
