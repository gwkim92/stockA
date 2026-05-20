# Data Operations Scheduler Activation Boundary

Date: 2026-05-04

## Decision

`data-operations-scheduler-activation-boundary` adds the repo-local wrapper contract that an actual scheduler can call later.

This is not scheduler installation. It does not create cron, launchd, GitHub Actions, hosted automation, production env files, or real credentials.

## Interface

Preflight:

```bash
scripts/run_data_operations_scheduler_job.sh \
  --env-file /secure/path/data-operations.env \
  --job-id macro-weekly \
  --run-date 2026-05-04 \
  --timeout-seconds 120 \
  --preflight-only \
  -- python3 -m stockanalysis.ingest.cli macro-batch-upsert \
    --fixtures-dir tests/fixtures \
    --series-id CPIAUCSL
```

Run:

```bash
scripts/run_data_operations_scheduler_job.sh \
  --env-file /secure/path/data-operations.env \
  --job-id macro-weekly \
  --run-date 2026-05-04 \
  -- python3 -m stockanalysis.ingest.cli macro-batch-upsert \
    --fixtures-dir tests/fixtures \
    --series-id CPIAUCSL \
    --series-id FEDFUNDS
```

Configured skip:

```bash
scripts/run_data_operations_scheduler_job.sh \
  --env-file /secure/path/data-operations.env \
  --job-id macro-weekly \
  --run-date 2026-12-25 \
  --skip-dates "2026-12-25" \
  --skip-reason market_holiday \
  -- python3 -m stockanalysis.ingest.cli macro-batch-upsert \
    --fixtures-dir tests/fixtures \
    --series-id CPIAUCSL
```

## Boundary Rules

- Env file must be trusted and stored outside the repository.
- The wrapper runs `scripts/check_data_operations_runtime_env.sh` before preflight or execution.
- `job_id` must exist in the cadence registry.
- Command after `--` is required, even in preflight.
- Preflight emits secret-free `data_operations_scheduler_preflight` JSON.
- Skip-date hit emits `data_operations_scheduler_skip` JSON and writes skip artifacts without running the child command.
- Non-skip execution delegates to `stockanalysis-ingest data-operations-run`, so stdout/stderr/metadata capture and argv redaction remain centralized.

## Artifact Boundary

Non-skip runs use the existing data operations artifact layout under:

```text
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT
```

Configured skip-date hits create:

```text
<artifact-root>/<YYYYMMDDTHHMMSSZ>_<job-id>_scheduler-skip/
  stdout.json
  stderr.log
  metadata.json
```

## Security Boundary

- The wrapper does not print env values.
- Preflight command argv uses `redact_command_argv`.
- Artifact runner metadata redacts sensitive flags, assignments, and URL userinfo.
- Verification asserts no scheduler activation artifacts exist under `.github/workflows`, `cron`, or `launchd`.

## Verification

Run:

```bash
bash scripts/verify_data_operations_scheduler_activation_boundary.sh
```

The verification checks syntax, targeted unit tests, missing command refusal, repo-inside env refusal, preflight redaction, skip artifact creation, non-skip artifact runner invocation, docs markers, AWH, and no scheduler activation artifacts.

## Not Implemented

- Scheduler install or activation.
- launchd/cron/GitHub Actions rendering.
- Production env file creation.
- Provider network credential validation.
- Alert receiver routing.
- DB schema changes.
- write APIs, RBAC, audit write model, broker/order flow, benchmark/scoring/evaluation changes.

## Follow-Up Implemented

`data-operations-scheduler-install-dry-run` renders a launchd plist and manifest to a repo-outside output dir without installing or activating the scheduler.

## Next Step

Next fixed task: `data-operations-scheduler-alert-boundary`.

That task should define how scheduler failures and stale/missing data operation runs become actionable alerts before actual scheduler activation.
