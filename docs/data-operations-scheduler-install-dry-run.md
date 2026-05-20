# Data Operations Scheduler Install Dry Run

Date: 2026-05-06

## Decision

`data-operations-scheduler-install-dry-run` renders a launchd scheduler artifact for a known data operations cadence job without installing or activating it.

This task does not write to `~/Library/LaunchAgents`, does not run `launchctl`, and does not create cron or GitHub Actions scheduler files.

## Interface

```bash
scripts/render_data_operations_scheduler_install.sh \
  --output-dir /tmp/data-operations-scheduler-rendered \
  --env-file /secure/path/data-operations.env \
  --job-id macro-weekly \
  --timeout-seconds 120 \
  -- python3 -m stockanalysis.ingest.cli macro-batch-upsert \
    --fixtures-dir tests/fixtures \
    --series-id CPIAUCSL \
    --series-id FEDFUNDS
```

The script prints the rendered manifest path.

## Rendered Files

The renderer writes the following under the caller-provided repo-outside output dir:

```text
<label>.plist
<label>.manifest.json
```

Default label:

```text
com.stockanalysis.data-operations.<job-id>
```

The plist calls:

```text
scripts/run_data_operations_scheduler_job.sh
```

with:

- `--env-file`
- `--job-id`
- `--timeout-seconds`
- command after `--`

## Schedule Boundary

Daily jobs render Monday through Friday launchd schedules using the cadence registry `expected_after_local`.

Weekly jobs render the configured weekday and time. For example, `macro-weekly` renders Monday 07:30 America/New_York as:

```json
[{ "Weekday": 2, "Hour": 7, "Minute": 30 }]
```

Monthly `first-business-day` jobs are explicitly rejected because launchd cannot safely express first business day without a calendar-aware wrapper.

## Security Boundary

- Output dir must be outside the repository.
- Env file must be outside the repository.
- Env values are not sourced, read, printed, or copied.
- Sensitive command argv such as `--api-key`, `DATABASE_URL=...`, or URL userinfo is rejected because plist files persist command text.
- Rendered files use mode `600`.

## Verification

Run:

```bash
bash scripts/verify_data_operations_scheduler_install_dry_run.sh
```

The verification checks script syntax, targeted unit tests, repo-inside path refusal, sensitive command refusal, monthly job rejection, rendered plist/manifest contents, no secret leakage, no host scheduler path writes, docs markers, and AWH.

## Not Implemented

- Actual launchd install.
- `launchctl bootstrap`.
- cron/GitHub Actions renderer.
- Production env file creation.
- Provider network credential validation.
- Alert receiver routing.
- DB schema changes.
- write APIs, RBAC, broker/order flow, benchmark/scoring/evaluation changes.

## Follow-Up Implemented

`data-operations-scheduler-alert-boundary` adds secret-free Prometheus-compatible alert rule references for missing, failed, stale, timeout, artifact missing, and preflight failure states.

## Next Step

Next fixed task: `data-operations-scheduler-activation-runbook`.

That task should define the final manual activation gate, rollback, disable, and evidence checklist before any actual scheduler install or `launchctl bootstrap`.
