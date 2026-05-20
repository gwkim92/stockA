# Data Operations Scheduler Activation Approval Gate

Date: 2026-05-11

## Decision

`data-operations-scheduler-activation-approval-gate` adds a machine-readable gate before any real Data Operations scheduler activation.

This task does not run `launchctl`, does not write to `~/Library/LaunchAgents`, and does not activate a scheduler.

## Interface

Pending approval:

```bash
scripts/check_data_operations_scheduler_activation_approval_gate.sh \
  --operator-dry-run-report /tmp/data-operations-operator-dry-run/evidence/operator-dry-run.json
```

With explicit approval record:

```bash
scripts/check_data_operations_scheduler_activation_approval_gate.sh \
  --operator-dry-run-report /tmp/data-operations-operator-dry-run/evidence/operator-dry-run.json \
  --approval-record /secure/path/data-operations-activation-approval.json \
  --output /secure/path/data-operations-activation-approval-gate.json
```

All input and output paths must be outside the repository.

## Approval Record Shape

```json
{
  "approval_record": "data_operations_scheduler_activation_approval",
  "approval_decision": "approved",
  "operator": "operator-handle",
  "approved_at": "2026-05-11T12:00:00Z",
  "job_id": "macro-weekly",
  "operator_dry_run_report": "/tmp/data-operations-operator-dry-run/evidence/operator-dry-run.json",
  "activation_window": "2026-05-11T12:00:00Z/2026-05-11T13:00:00Z",
  "rollback_owner": "operator-handle",
  "acknowledged_commands": [
    "install -m 600",
    "launchctl bootstrap",
    "launchctl kickstart",
    "launchctl print"
  ],
  "acknowledged_risks": [
    "host_scheduler_state_change",
    "recurring_data_operation_execution",
    "rollback_required_if_first_run_fails"
  ]
}
```

## Gate Outcomes

No approval record returns:

```json
{
  "approval_gate": "blocked_pending_manual_approval",
  "activation_allowed": false,
  "launchctl_executed": false
}
```

Valid approval record returns:

```json
{
  "approval_gate": "approved_for_manual_activation",
  "activation_allowed": true,
  "launchctl_executed": false
}
```

`activation_allowed=true` means only that the evidence and approval metadata are valid. It does not execute activation.

## Safety Boundary

- Operator dry-run report must be outside the repository.
- Approval record must be outside the repository.
- Gate output must be outside the repository when `--output` is used.
- Approval record must match the same `job_id` and operator dry-run report path.
- Approval record must acknowledge activation commands and rollback risk.
- Raw env values, DB URLs, API keys, bearer tokens, and passwords are rejected from approval metadata.
- No script in this task runs `launchctl`.

## Verification

Run:

```bash
bash scripts/verify_data_operations_scheduler_activation_approval_gate.sh
```

The verification generates a repo-outside operator dry-run report, checks blocked output without approval, checks approved output with a fixture approval record, confirms fake secret values do not leak, refuses repo-inside evidence paths, checks docs/roadmap markers, and runs AWH.

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

Completed next task: `data-operations-live-scheduler-activation-request`.

That task presents repo-outside dry-run evidence as a `pending_explicit_user_approval` packet. The next fixed task is `data-operations-live-scheduler-activation-user-decision`, which must record approve or deny before any live host scheduler activation command is allowed.
