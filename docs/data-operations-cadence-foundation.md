# Data Operations Cadence Foundation

Date: 2026-05-03

## Decision

`data-operations-cadence-foundation` starts the Data Operations Loop by adding a repo-owned cadence registry for recurring data jobs.

The registry lives in `src/stockanalysis/operations/cadence.py` and is exposed through:

- `stockanalysis-ingest data-operations-cadence`
- `build_data_operations_cadence_report()`
- `render_data_operations_expected_jobs_sql_values()`
- `/api/data-health` live SQL expected job rows

This is not scheduler activation. It does not create cron, launchd, hosted automations, deployment manifests, or credentials. It defines what should run, when it becomes stale, what artifact policy applies, and how data-health should interpret latest `ops.pipeline_run` state.

## Cadence Groups

Daily jobs:

- `market_price_upsert`: refresh market price bars after US market close.
- `portfolio_position_snapshot_upsert`: ingest the operator-provided portfolio snapshot.
- `portfolio_remediation_daily_automation`: run review/ticket daily operating loop.

Weekly jobs:

- `macro_upsert`: refresh default macro series.
- `sec_filings_upsert`: sync SEC filing metadata.
- `event_intelligence_llm_extract`: structure source documents with the AI extraction path.
- `cycle_state_snapshot`: refresh theme cycle state context.

Monthly jobs:

- `performance_outcome_schedule_bootstrap`: capture due long-horizon outcomes.
- `portfolio_attribution_bootstrap`: update portfolio attribution after outcomes and prices are available.

## Artifact Boundary

The registry introduces one repo-wide artifact root env name:

```text
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT
```

Each recurring job should persist:

- stdout JSON summary
- stderr log
- runner metadata such as command, started_at, ended_at, exit_code
- optional domain artifacts, for example SEC raw filing files or AI extraction artifact ids

The env variable is only a name in this task. It does not commit a local path, production path, or secret.

## Data Health Boundary

`/api/data-health` live read now joins a static `expected_jobs` CTE against `ops.pipeline_run`.

Per expected job it emits:

- `job_id`
- `domain`
- `cadence`
- `expected_after_local`
- `stale_after_hours`
- `artifact_policy`
- `latest_status`
- `health_status`
- `latest_run_id`
- `finished_at`

`health_status` is computed as:

- `missing`: no latest run exists.
- `failed`: latest run failed.
- `running`: latest run is still `started` or `running`.
- `stale`: latest successful run ended before the stale threshold.
- `ok`: latest run exists and is within the threshold.

`overall_status` becomes `attention_required` when any expected job is missing, stale, or failed.

## CLI

Render the registry:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli data-operations-cadence
```

Filter by cadence:

```bash
PYTHONPATH=src python3 -m stockanalysis.ingest.cli data-operations-cadence --cadence weekly
```

## Follow-Up Implemented

`data-operations-artifact-runner` adds the generic repo-local wrapper that captures stdout, stderr, and metadata under `STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT`.

`data-operations-runtime-env-readiness` adds the repo-outside runtime env activation gate for database, providers, portfolio snapshot source, LLM provider, market price history dependency, and artifact root.

`data-operations-runtime-smoke` runs representative fixture-backed runtime ingest through the env readiness gate and artifact runner.

## Not Implemented

- Actual scheduler activation.
- Provider network credential smoke.
- Alert receiver routing for data operations.
- DB schema changes.
- Real credentials.
- Benchmark, scoring, evaluation split, auth/RBAC, write APIs, or broker/order flow.

## Next Step

Next fixed task: `data-operations-scheduler-activation-boundary`.

That task should define how the cadence registry is invoked by an actual scheduler without committing host scheduler artifacts or secrets.
