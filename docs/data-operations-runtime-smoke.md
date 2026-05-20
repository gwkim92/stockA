# Data Operations Runtime Smoke

Date: 2026-05-04

## Decision

`data-operations-runtime-smoke` adds a scheduler-free runtime smoke for the Data Operations Loop.

The smoke composes two existing boundaries:

- `scripts/check_data_operations_runtime_env.sh`
- `stockanalysis-ingest data-operations-run`

It proves a trusted repo-outside env file can pass readiness and a known cadence job can run through the artifact runner with stdout, stderr, metadata, and optional stdout JSON capture.

## Interface

```bash
scripts/smoke_data_operations_runtime.sh \
  --env-file /secure/path/data-operations.env \
  --job-id macro-weekly \
  --timeout-seconds 120 \
  -- python3 -m stockanalysis.ingest.cli macro-batch-upsert \
    --fixtures-dir tests/fixtures \
    --series-id CPIAUCSL \
    --series-id FEDFUNDS
```

The wrapper prints:

```json
{
  "report_name": "data_operations_runtime_smoke",
  "runtime_smoke": "passed",
  "runtime_env_readiness": "passed",
  "job_id": "macro-weekly",
  "scheduler_activation": "not_activated"
}
```

## Representative Job

The first representative job is `macro-weekly`.

The verification command runs fixture-backed `macro-batch-upsert` against disposable Docker Postgres. This exercises:

- env readiness gate
- DB command inheritance through the trusted env file
- canonical migration/seed boundary
- `ops.pipeline_run` writes
- stdout/stderr/metadata artifact capture
- stdout JSON normalization
- known cadence metadata

It intentionally does not call FRED over the network. Provider credential network validation remains a separate future task.

## Secret Boundary

- Env file must be outside the repository.
- The wrapper does not print env values.
- The combined smoke report exposes only status, job id, cadence metadata, artifact paths, env group names, and scheduler activation status.
- Artifact runner metadata redacts sensitive command argv.

## Verification

Run:

```bash
bash scripts/verify_data_operations_runtime_smoke.sh
```

The verification starts disposable Postgres, applies migrations/seeds, creates a repo-outside temp env, runs the smoke wrapper, checks macro rows and pipeline runs, checks artifact files, checks secret non-leakage, and runs AWH verification.

## Not Implemented

- Actual scheduler activation.
- cron, launchd, GitHub Actions, hosted automations.
- Production env file creation.
- Provider network credential validation.
- Alert receiver routing.
- DB schema changes.
- write APIs, RBAC, audit write model, broker/order flow, benchmark/scoring/evaluation changes.

## Follow-Up Implemented

`data-operations-scheduler-activation-boundary` adds the generic wrapper contract that an actual scheduler can call later with repo-outside env readiness, preflight, skip-date handling, and artifact runner invocation.

## Next Step

Next fixed task: `data-operations-scheduler-install-dry-run`.

That task should render but not install the host scheduler artifact that calls the generic wrapper.
