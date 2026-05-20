# Manual Host Scheduler Activation Explicit Approval

Date: 2026-05-15

## Decision

`manual-host-scheduler-activation-explicit-approval` turns the confirmed host activation execution report into an exact-command approval packet.

This task does not run `launchctl`, does not write `~/Library/LaunchAgents`, and does not execute child data operation commands.

## Interface

```bash
scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh \
  --host-activation-execution-report /secure/path/host-activation-execution.json \
  --output /secure/path/manual-host-activation-approval.json
```

Optional approval:

```bash
scripts/prepare_manual_host_scheduler_activation_explicit_approval.sh \
  --host-activation-execution-report /secure/path/host-activation-execution.json \
  --approval-record /secure/path/approve-exact-host-commands.json \
  --output /secure/path/manual-host-activation-approval.json
```

All input and output paths must be outside the repository.

## Outcomes

- `blocked_pending_exact_host_command_approval`
- `aborted_manual_host_scheduler_activation`
- `approved_for_manual_operator_host_activation_not_executed_by_codex`

Even the approved outcome keeps:

```json
{
  "codex_host_mutation_allowed": false,
  "host_install_path_written": false,
  "launchctl_executed": false,
  "host_activation_execution_performed": false
}
```

## Approval Record Shape

```json
{
  "approval_record": "manual_host_scheduler_activation_explicit_approval",
  "approval": "approve_exact_host_scheduler_activation",
  "approver": "operator-handle",
  "approved_at": "2026-05-15T09:30:00Z",
  "job_id": "macro-weekly",
  "host_activation_execution_report": "/secure/path/host-activation-execution.json",
  "approval_scope": "manual_host_scheduler_activation",
  "acknowledged_execution_gate": "confirmed_for_manual_host_mutation_not_executed_by_this_task",
  "approved_exact_execution_commands": [
    "install -m 600 ...",
    "launchctl bootstrap ...",
    "launchctl kickstart ...",
    "launchctl print ..."
  ],
  "approved_exact_rollback_commands": [
    "launchctl bootout ...",
    "launchctl print ..."
  ],
  "acknowledged_mutation_boundary": [
    "host_launchagents_write",
    "launchctl_bootstrap",
    "launchctl_kickstart",
    "launchctl_print",
    "rollback_required_if_activation_fails",
    "recurring_data_operation_execution"
  ],
  "acknowledged_operator_responsibility": [
    "operator_runs_commands_outside_codex",
    "operator_records_exit_statuses",
    "operator_collects_launchctl_print_evidence",
    "operator_collects_first_run_artifacts",
    "operator_can_execute_rollback"
  ]
}
```

Use `abort_exact_host_scheduler_activation` instead of `approve_exact_host_scheduler_activation` to explicitly block host mutation.

## Verification

Run:

```bash
bash scripts/verify_manual_host_scheduler_activation_explicit_approval.sh
```

The verification uses repo-outside host activation execution evidence, checks missing/approve/abort outcomes, rejects command drift, rejects repo-inside paths and secret-like values, checks docs/roadmap markers, and runs AWH.

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

The next physical action is still manual host scheduler activation outside Codex, after the user approves the exact commands. This task intentionally stops before that mutation.
