# Data Operations Scheduler Operator Dry Run

Date: 2026-05-11

## Decision

`data-operations-scheduler-operator-dry-run` rehearses the Data Operations scheduler activation runbook without mutating host scheduler state.

This task does not run `launchctl`, does not write to `~/Library/LaunchAgents`, does not install a scheduler, and does not execute the child data operation command.

## Interface

```bash
scripts/dry_run_data_operations_scheduler_operator_flow.sh \
  --env-file /secure/path/data-operations.env \
  --job-id market-price-daily \
  --output-dir /tmp/data-operations-operator-dry-run \
  --run-date 2026-05-15 \
  --timeout-seconds 600 \
  -- python3 -m stockanalysis.operations.cli market-price-daily-run \
    --skip-if-fresh
```

The script prints the final `operator-dry-run.json` path.

## Evidence Bundle

The output directory must be outside the repository. The dry-run writes:

```text
<output-dir>/evidence/env-readiness.json
<output-dir>/evidence/scheduler-preflight.json
<output-dir>/evidence/alert-rule-validation.txt
<output-dir>/evidence/operator-dry-run.json
<output-dir>/rendered/<label>.plist
<output-dir>/rendered/<label>.manifest.json
```

## Checked Steps

- Runtime env readiness through `scripts/check_data_operations_runtime_env.sh`.
- Scheduler preflight through `scripts/run_data_operations_scheduler_job.sh --preflight-only`.
- Launchd install dry-run rendering through `scripts/render_data_operations_scheduler_install.sh`.
- Alert rule validation through `scripts/validate_data_operations_alert_rules.py`.
- Evidence report construction through `stockanalysis.operations.scheduler_operator_dry_run`.

## Safety Boundary

- Env file must be outside the repository.
- Output dir must be outside the repository.
- The child command after `--` is not executed.
- `launchctl` is not executed.
- Host LaunchAgents paths are not written.
- Final report excludes raw env values and records only evidence file paths.

## Report Shape

The final report uses:

```json
{
  "report_name": "data_operations_scheduler_operator_dry_run",
  "operator_dry_run": "passed",
  "scheduler_activation": "not_installed",
  "launchctl_executed": false,
  "child_command_executed": false,
  "requires_manual_approval": true
}
```

## Verification

Run:

```bash
bash scripts/verify_data_operations_scheduler_operator_dry_run.sh
```

The verification creates a repo-outside temp env file, positions CSV, artifact root, and output dir, then asserts the evidence bundle exists, no fake secret values leak into the final report, repo-inside env/output paths are rejected, docs markers exist, roadmap markers are current, and AWH passes.

## Not Implemented

- Actual scheduler activation.
- `launchctl bootstrap`.
- Host LaunchAgents writes.
- Provider network credential validation.
- Alertmanager receiver routing.
- Production Prometheus install.
- DB schema changes.
- write APIs, RBAC, broker/order flow, benchmark/scoring/evaluation changes.

## Next Step

Follow-up implemented: `data-operations-scheduler-activation-approval-gate`.

It validates operator dry-run evidence and blocks activation unless a repo-outside explicit approval record is present.

Next fixed task: `data-operations-live-scheduler-activation-request`.

That task should present real repo-outside dry-run evidence and request explicit user approval before any live host scheduler activation command is run.
