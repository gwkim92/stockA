# Data Operations Live Scheduler Activation Request

Date: 2026-05-11

## Decision

`data-operations-live-scheduler-activation-request` creates a user-facing request packet after the activation approval gate is approved.

This task does not run `launchctl`, does not write to `~/Library/LaunchAgents`, and does not activate a scheduler.

## Interface

With explicit operator dry-run evidence:

```bash
scripts/request_data_operations_live_scheduler_activation.sh \
  --approval-gate-report /secure/path/data-operations-activation-approval-gate.json \
  --operator-dry-run-report /tmp/data-operations-operator-dry-run/evidence/operator-dry-run.json \
  --output /secure/path/data-operations-live-activation-request.json
```

Deriving the operator dry-run path from the approval gate:

```bash
scripts/request_data_operations_live_scheduler_activation.sh \
  --approval-gate-report /secure/path/data-operations-activation-approval-gate.json \
  --output /secure/path/data-operations-live-activation-request.json
```

All input and output paths must be outside the repository.

## Request Outcome

Valid approved gate evidence returns:

```json
{
  "activation_request": "pending_explicit_user_approval",
  "requested_user_decision_values": [
    "approve_live_scheduler_activation",
    "deny_live_scheduler_activation"
  ],
  "launchctl_executed": false,
  "host_install_path_written": false
}
```

`pending_explicit_user_approval` means activation is still blocked. A future user decision task must record approve or deny before any live host scheduler activation command is allowed.

## Safety Boundary

- Approval gate report must be outside the repository.
- Operator dry-run report must be outside the repository.
- Request output must be outside the repository when `--output` is used.
- Approval gate must be `approved_for_manual_activation`.
- Request output must remain `pending_explicit_user_approval`.
- Raw env values, DB URLs, API keys, bearer tokens, and passwords are rejected from request metadata.
- Command previews may mention `launchctl` for operator review, but no script in this task runs `launchctl`.

## Verification

Run:

```bash
bash scripts/verify_data_operations_live_scheduler_activation_request.sh
```

The verification generates a repo-outside operator dry-run report, creates an approved activation gate report, renders the pending request packet, confirms fake secret values do not leak, rejects pending gate input, refuses repo-inside evidence paths, checks docs/roadmap markers, and runs AWH.

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

Completed next task: `data-operations-live-scheduler-activation-user-decision`.

That task validates a user decision record with either `approve_live_scheduler_activation` or `deny_live_scheduler_activation`. The next fixed task is `data-operations-live-scheduler-activation-final-preflight`, which must re-check current evidence before any separate host activation task is considered.
