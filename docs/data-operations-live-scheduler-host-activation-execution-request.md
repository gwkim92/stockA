# Data Operations Live Scheduler Host Activation Execution Request

Date: 2026-05-11

## Decision

`data-operations-live-scheduler-host-activation-execution-request` creates a JSON request packet for explicit execution approval after a host activation plan is reviewed.

This task does not run `launchctl`, does not write to `~/Library/LaunchAgents`, and does not activate a scheduler.

## Interface

```bash
scripts/request_data_operations_live_scheduler_host_activation_execution.sh \
  --host-activation-plan-report /secure/path/host-activation-plan.json \
  --output /secure/path/host-activation-execution-request.json \
  --request-note "operator reviewed host activation plan"
```

All input and output paths must be outside the repository.

## Request Outcome

Ready host activation plan returns:

```json
{
  "execution_request": "pending_explicit_execution_approval",
  "requires_explicit_execution_approval": true,
  "host_activation_execution_allowed_in_this_task": false,
  "launchctl_executed": false
}
```

The request packet includes:

- requested user decision values: `approve_host_activation_execution`, `deny_host_activation_execution`
- command previews copied from the reviewed host activation plan
- rollback command previews copied from the reviewed host activation plan
- acknowledgement requirements for host mutation risk

## Safety Boundary

- Host activation plan report must be outside the repository.
- Output path must be outside the repository.
- Command previews may mention `install` and `launchctl`, but the script must not execute them.
- Passing request only allows a future execution decision task.
- Raw env values, DB URLs, API keys, bearer tokens, and passwords are rejected from request metadata.
- No script in this task runs `launchctl` or writes host LaunchAgents.

## Verification

Run:

```bash
bash scripts/verify_data_operations_live_scheduler_host_activation_execution_request.sh
```

The verification builds the repo-outside evidence chain, creates a host activation plan, creates an execution request packet, confirms fake secret values do not leak, refuses malformed plans and repo-inside paths, checks docs/roadmap markers, and runs AWH.

## Not Implemented

- Actual scheduler activation.
- `launchctl bootstrap`.
- Host LaunchAgents writes.
- Host activation execution decision record validation.
- Provider network credential validation.
- Alertmanager receiver routing.
- Production Prometheus install.
- DB schema changes.
- write APIs, RBAC, broker/order flow, benchmark/scoring/evaluation changes.

## Handoff Status

Host activation execution request hands off to `data-operations-live-scheduler-host-activation-execution-decision`, which is now implemented.

Current fixed next task: `data-operations-live-scheduler-host-activation-execution-final-preflight`.

That task should revalidate the approved execution decision, reviewed plan, and fresh runtime readiness immediately before any execution task. Actual host mutation remains forbidden until a later explicit execution task.
