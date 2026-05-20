# Manual Host Scheduler Activation Preflight

Date: 2026-05-15

## Decision

`manual-host-scheduler-activation-preflight` checks the approved exact-command packet and fresh runtime env readiness immediately before any external manual scheduler activation.

This task does not run `launchctl`, does not write `~/Library/LaunchAgents`, and does not execute child data operation commands.

## Interface

```bash
scripts/preflight_manual_host_scheduler_activation.sh \
  --manual-approval-report /secure/path/manual-host-activation-approval.json \
  --env-file /secure/path/data-operations.env \
  --output-dir /secure/path/manual-host-activation-preflight
```

All input and output paths must be outside the repository.

## Outcomes

- `blocked_manual_approval_not_ready`
- `blocked_runtime_env_not_ready`
- `passed_ready_for_external_manual_host_scheduler_activation`

Even the passed outcome keeps:

```json
{
  "codex_host_mutation_allowed": false,
  "host_install_path_written": false,
  "launchctl_executed": false,
  "host_activation_execution_performed": false
}
```

## Output Files

The wrapper writes:

- `manual-host-scheduler-activation-preflight.json`
- `evidence/runtime-env-readiness.json`

## Passed Handoff

When passed, the report includes:

- exact execution commands
- exact rollback commands
- operator evidence requirements
- `manual_operator_may_execute_exact_commands=true`

The operator evidence requirements are:

- record install exit status
- record `launchctl bootstrap` exit status
- record `launchctl kickstart` exit status
- capture `launchctl print` output
- capture first-run artifact directory
- capture rollback evidence if activation fails

## Verification

Run:

```bash
bash scripts/verify_manual_host_scheduler_activation_preflight.sh
```

The verification uses repo-outside approval/env fixtures, checks passed/blocked outcomes, rejects repo-inside paths and secret-like values, checks docs/roadmap markers, and runs AWH.

## Not Implemented

- Actual scheduler activation.
- `launchctl bootstrap`.
- Host LaunchAgents writes.
- Provider network credential validation.
- Alertmanager receiver routing.
- Production Prometheus install.
- DB schema changes.
- write APIs, RBAC, broker/order flow, benchmark/scoring/evaluation changes.

## Handoff Status

The next physical action is still external manual host scheduler activation after exact command approval and fresh env readiness. This task intentionally stops before that mutation.
