# Data Operations Live Scheduler Host Activation Plan

Date: 2026-05-11

## Decision

`data-operations-live-scheduler-host-activation-plan` creates JSON and Markdown operator review artifacts for live scheduler activation after final preflight passes.

This task does not run `launchctl`, does not write to `~/Library/LaunchAgents`, and does not activate a scheduler.

## Interface

```bash
scripts/plan_data_operations_live_scheduler_host_activation.sh \
  --final-preflight-report /secure/path/final-preflight.json \
  --output-dir /secure/path/host-activation-plan
```

Optional explicit activation request:

```bash
scripts/plan_data_operations_live_scheduler_host_activation.sh \
  --final-preflight-report /secure/path/final-preflight.json \
  --activation-request-report /secure/path/live-activation-request.json \
  --output-dir /secure/path/host-activation-plan
```

All input and output paths must be outside the repository.

## Plan Outcome

Passing final preflight returns:

```json
{
  "host_activation_plan": "ready_for_execution_request",
  "activation_allowed_for_execution_request": true,
  "host_activation_execution_allowed_in_this_task": false,
  "launchctl_executed": false
}
```

The wrapper writes:

- `host-activation-plan.json`
- `host-activation-plan.md`

## Safety Boundary

- Final preflight and activation request reports must be outside the repository.
- Output dir must be outside the repository.
- Command previews may mention `install` and `launchctl`, but the script must not execute them.
- Passing plan only allows a future execution request task.
- Raw env values, DB URLs, API keys, bearer tokens, and passwords are rejected from plan metadata.
- No script in this task runs `launchctl` or writes host LaunchAgents.

## Verification

Run:

```bash
bash scripts/verify_data_operations_live_scheduler_host_activation_plan.sh
```

The verification builds the repo-outside evidence chain, runs final preflight, creates JSON/Markdown host activation plan artifacts, confirms fake secret values do not leak, refuses denied preflight and repo-inside paths, checks docs/roadmap markers, and runs AWH.

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

Host activation plan hands off to `data-operations-live-scheduler-host-activation-execution-request`, which is now implemented.

Current fixed next task: `data-operations-live-scheduler-host-activation-execution-decision`.

That task should validate approve/deny records for the execution request. Actual host mutation remains forbidden until a later explicit execution task.
