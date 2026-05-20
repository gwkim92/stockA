# Task Plan

1. Create `data-operations-cadence-foundation` contract/plan/handoff/review documents.
2. Add `src/stockanalysis/operations/cadence.py` with daily/weekly/monthly cadence registry, report function, and SQL values renderer.
3. Add `tests/test_data_operations_cadence.py`.
4. Add `stockanalysis-ingest data-operations-cadence --cadence ...` CLI support and test it.
5. Extend frontend data-health live SQL to join expected jobs from the cadence registry against `ops.pipeline_run`.
6. Extend DataHealth payload/example/type with job metadata and `health_status`.
7. Add `scripts/verify_data_operations_cadence_foundation.sh`.
8. Update README, verification plan, roadmap, AGENTS, and dependent verification scripts.
9. Run task verification, roadmap verification, full unittest, AWH, and diff check.
