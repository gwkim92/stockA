# Data Operations Artifact Runner

Date: 2026-05-03

## Decision

`data-operations-artifact-runner` adds a repo-local generic runner for data operations jobs.

The runner executes one command for a known cadence `job_id` and writes artifacts under:

```text
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT
```

This is still not scheduler activation. It does not create cron, launchd, hosted automations, deployment manifests, production env files, or credentials.

## Interfaces

Python:

```python
from stockanalysis.operations.artifact_runner import run_data_operation_artifact_command
```

CLI:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli \
  data-operations-run \
  --job-id macro-weekly \
  --artifact-root /tmp/stockanalysis-data-ops \
  -- python3 -m stockanalysis.ingest.cli data-operations-cadence --cadence weekly
```

If `--artifact-root` is omitted, the runner reads `STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT`.

## Artifact Layout

Each run creates:

```text
<artifact-root>/<YYYYMMDDTHHMMSSZ>_<job-id>/
  stdout.txt
  stdout.json      # only when stdout is valid JSON
  stderr.log
  metadata.json
```

`metadata.json` includes:

- `job_id`
- `pipeline_name`
- `domain`
- `cadence`
- `status`
- `exit_code`
- `timeout`
- `started_at`
- `ended_at`
- `duration_ms`
- artifact paths
- redacted command argv

## Status Rules

- `succeeded`: child command exit code is 0.
- `failed`: child command exits non-zero.
- `timeout`: child command exceeds `--timeout-seconds`; runner returns exit code 124.

The CLI prints `metadata.json` content to stdout and returns the child exit code. This lets a future scheduler fail naturally while still preserving artifacts.

## Secret Boundary

The runner does not persist environment variables.

Command argv metadata is redacted for:

- token/password/secret/read-token/api-key flags
- sensitive `KEY=value` assignments such as `DATABASE_URL=...`
- URL userinfo, for example `postgresql://user:password@host/db`

This is a safety boundary, not permission to pass secrets through command args. Operators should still prefer env files outside the repository.

## Verification

Run:

```bash
bash scripts/verify_data_operations_artifact_runner.sh
```

The verification compiles the runner, runs unit tests, executes a CLI smoke into a temp artifact root, and checks docs/roadmap/handoff markers.

## Follow-Up Implemented

`data-operations-runtime-env-readiness` adds the repo-outside runtime env activation gate for database, providers, portfolio snapshot source, LLM provider, and artifact root.

`data-operations-runtime-smoke` runs representative fixture-backed runtime ingest through the env readiness gate and artifact runner.

## Not Implemented

- Production scheduler activation.
- Provider network credential smoke.
- Alert receiver routing.
- DB schema changes.
- Real credentials.
- write APIs, RBAC, audit write model, broker/order flow, benchmark/scoring/evaluation changes.

## Next Step

Next fixed task: `data-operations-scheduler-activation-boundary`.

That task should define how the cadence registry is invoked by an actual scheduler without committing host scheduler artifacts or secrets.
