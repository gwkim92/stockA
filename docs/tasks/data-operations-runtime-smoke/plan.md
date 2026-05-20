# Implementation Plan

## Goal

Add a local runtime smoke that proves env readiness, artifact runner execution, DB-backed fixture ingest, and artifact capture work together before scheduler activation.

## Steps

1. Add `src/stockanalysis/operations/runtime_smoke.py`.
2. Add `tests/test_data_operations_runtime_smoke.py`.
3. Add `scripts/smoke_data_operations_runtime.sh`.
4. Add `scripts/verify_data_operations_runtime_smoke.sh` using disposable Docker Postgres and fixture macro batch.
5. Add docs and update roadmap/README/verification/AGENTS.
6. Run targeted and full verification.

## Representative Job

- Job id: `macro-weekly`.
- Command: `stockanalysis-ingest macro-batch-upsert --fixtures-dir tests/fixtures --series-id CPIAUCSL --series-id FEDFUNDS`.
- Reason: it exercises DB writes, `ops.pipeline_run`, fixture-based external data boundary, stdout JSON artifact capture, stderr artifact capture, and known cadence metadata without remote provider calls.

## Security

- Env file remains repo-outside.
- The smoke wrapper does not print env values.
- Artifact metadata comes from `data-operations-run`, which already redacts sensitive command argv.
- The combined smoke report exposes only status, job id, artifact paths, env group names, and non-secret readiness metadata.
