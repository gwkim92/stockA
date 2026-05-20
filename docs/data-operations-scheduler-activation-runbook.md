# Data Operations Scheduler Activation Runbook

Date: 2026-05-06

## Decision

`data-operations-scheduler-activation-runbook` defines the manual operating procedure required before enabling recurring Data Operations scheduler jobs.

This task does not execute `launchctl`, does not write to `~/Library/LaunchAgents`, and does not install a scheduler. Commands below are reference commands for a future explicitly approved operator action.

## Activation Boundary

Actual activation is allowed only after all of the following are true:

- The operator explicitly approves activation for one `job_id`.
- The env file is outside the repository and passes `scripts/check_data_operations_runtime_env.sh`.
- The artifact root is outside the repository and writable by the scheduler user.
- `scripts/run_data_operations_scheduler_job.sh --preflight-only` passes for the target command.
- `scripts/render_data_operations_scheduler_install.sh` renders a plist and manifest into a repo-outside directory.
- `scripts/validate_data_operations_alert_rules.py ops/observability/data-operations-alert-rules.yml` passes.
- The operator has a rollback window and can observe the first run artifact.

## Required Inputs

- `JOB_ID`: cadence registry job id, for example `macro-weekly`.
- `ENV_FILE`: trusted runtime env file outside the repository.
- `OUTPUT_DIR`: repo-outside directory for rendered scheduler files.
- `TIMEOUT_SECONDS`: child command timeout.
- `COMMAND`: data operation command after `--`.
- `LABEL`: default `com.stockanalysis.data-operations.<job-id>`.
- `HOST_PLIST_PATH`: `$HOME/Library/LaunchAgents/<label>.plist`.

Do not place raw tokens, DB URLs, API keys, portfolio identifiers, thesis identifiers, or broker/account identifiers in the plist command arguments.

## Market Price Daily Defaults

For `JOB_ID=market-price-daily`, use the scheduler-friendly operations boundary instead of passing watchlist and ledger paths directly in the launchd command:

```bash
COMMAND=(
  stockanalysis-operations
  market-price-daily-run
  --skip-if-fresh
)
```

The command reads these values from the repo-outside env file:

- `STOCKANALYSIS_MARKET_PRICE_PROVIDER`, expected local MVP value: `twelve_data`.
- `STOCKANALYSIS_TWELVE_DATA_API_KEY` for Twelve Data, or `STOCKANALYSIS_ALPHA_VANTAGE_API_KEY` for Alpha Vantage fallback.
- `STOCKANALYSIS_MARKET_PRICE_WATCHLIST_CSV`, expected local MVP path: `/private/tmp/stockanalysis-runtime/watchlists/twelve-data-expanded-watchlist.csv`.
- `STOCKANALYSIS_MARKET_PRICE_BUDGET_LEDGER_PATH`, expected local MVP path: `/private/tmp/stockanalysis-runtime/twelve-data-budget-ledger.json`.
- Optional request controls: `STOCKANALYSIS_MARKET_PRICE_DAILY_BUDGET`, `STOCKANALYSIS_MARKET_PRICE_MAX_REQUESTS_PER_RUN`, `STOCKANALYSIS_MARKET_PRICE_THROTTLE_SECONDS`, `STOCKANALYSIS_MARKET_PRICE_OUTPUTSIZE`.
- Optional freshness controls:
  - `DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_FRESHNESS_DATE`: explicit override for a single target date.
  - `DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_FRESHNESS_POLICY`: defaults to `latest_completed_us_market_day`; `scheduler_run_date` is available only for deliberate legacy behavior.
  - `DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_NON_TRADING_DATES`: comma or space separated market holidays/non-trading dates maintained outside the repository.
  - `DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_DATA_READY_LOCAL_TIME`: default `18:30`, interpreted in `America/New_York`.

The scheduler wrapper exports `DATA_OPERATIONS_SCHEDULER_RUN_DATE` to the child process. If `DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_FRESHNESS_DATE` is not set, `market-price-daily-run` now resolves the freshness target through `latest_completed_us_market_day`: weekdays only, explicit non-trading dates skipped, and New York local data-ready time used when no scheduler run date is present. This keeps repeat runs from spending provider calls on already-fresh symbols without expecting same-day bars before the US market day is complete.

## Stop Conditions

Stop and do not activate if any condition occurs:

- Runtime env readiness fails.
- Scheduler preflight fails.
- Install dry-run rejects the command or output path.
- Rendered plist or manifest contains a secret-like value.
- Alert rule validation fails.
- Existing data-health shows unresolved failed, missing, or stale jobs that the operator cannot explain.
- The operator cannot run rollback during the activation window.

## Preflight Sequence

1. Validate env readiness:

```bash
scripts/check_data_operations_runtime_env.sh --env-file "$ENV_FILE"
```

2. Validate scheduler preflight:

```bash
scripts/run_data_operations_scheduler_job.sh \
  --env-file "$ENV_FILE" \
  --job-id "$JOB_ID" \
  --timeout-seconds "$TIMEOUT_SECONDS" \
  --preflight-only \
  -- "${COMMAND[@]}"
```

3. Render install artifacts into a repo-outside directory:

```bash
scripts/render_data_operations_scheduler_install.sh \
  --output-dir "$OUTPUT_DIR" \
  --env-file "$ENV_FILE" \
  --job-id "$JOB_ID" \
  --timeout-seconds "$TIMEOUT_SECONDS" \
  -- "${COMMAND[@]}"
```

4. Validate alert rule reference:

```bash
python3 scripts/validate_data_operations_alert_rules.py \
  ops/observability/data-operations-alert-rules.yml
```

## Manual Approval Gate

Before host activation, record the following outside the repository:

- operator name or handle
- approval timestamp with timezone
- `JOB_ID`
- rendered plist path
- rendered manifest path
- activation window
- rollback owner
- expected first run artifact directory

If this record is absent, do not run the activation commands.

## Activation Reference Commands

These commands are reference-only in this repository. Do not run them from an automated verification script.

```bash
install -m 600 "$OUTPUT_DIR/$LABEL.plist" "$HOST_PLIST_PATH"
launchctl bootstrap "gui/$(id -u)" "$HOST_PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/$LABEL"
launchctl print "gui/$(id -u)/$LABEL"
```

## First-Run Evidence

After activation, collect evidence outside the repository:

- `launchctl print "gui/$(id -u)/$LABEL"` output.
- The first scheduler run artifact directory.
- `stdout.json`, `stderr.log`, and `metadata.json` from the first run.
- Env readiness output with secret values redacted.
- Install manifest path and rendered plist path.
- Data-health response showing the target job is not missing after the first run.
- Alert state for the data operations alert rule group.

## Rollback

Rollback removes the loaded launchd job and preserves evidence.

```bash
launchctl bootout "gui/$(id -u)" "$HOST_PLIST_PATH"
launchctl print "gui/$(id -u)/$LABEL"
```

Expected rollback evidence:

- `bootout` exit status.
- `launchctl print` output showing the job is absent or not loaded.
- Preserved first-run artifacts and stderr logs.
- Reason for rollback.

## Disable

Disable is used when the recurring job should remain off after rollback or during an extended incident.

```bash
launchctl bootout "gui/$(id -u)" "$HOST_PLIST_PATH"
mv "$HOST_PLIST_PATH" "$HOST_PLIST_PATH.disabled.$(date +%Y%m%dT%H%M%S)"
```

If the job is intentionally re-enabled later, repeat the preflight sequence before activation.

## Evidence Checklist

- [ ] runtime env readiness passed.
- [ ] scheduler preflight passed.
- [ ] install dry-run rendered plist and manifest outside the repository.
- [ ] alert rule validation passed.
- [ ] manual approval record exists outside the repository.
- [ ] host plist was installed with mode `600`.
- [ ] `launchctl bootstrap` exit status recorded.
- [ ] first run artifact directory captured.
- [ ] first run `metadata.json` status reviewed.
- [ ] data-health state reviewed after first run.
- [ ] rollback command tested or rollback owner confirmed.

## Not Implemented

- Actual scheduler activation.
- Host LaunchAgents writes.
- Alertmanager receiver routing.
- Production Prometheus install.
- Provider network credential validation.
- DB schema changes.
- write APIs, RBAC, broker/order flow, benchmark/scoring/evaluation changes.

## Next Step

Follow-up implemented: `data-operations-scheduler-operator-dry-run`.

It rehearses this runbook with repo-outside temporary paths and no host scheduler mutation before any real `launchctl bootstrap` is approved.

Next fixed task: `data-operations-scheduler-activation-approval-gate`.

That task should present the operator dry-run evidence and require explicit user approval before any real host scheduler activation.
