# Data Operations Live Scheduler Activation Final Preflight

Date: 2026-05-11

## Decision

`data-operations-live-scheduler-activation-final-preflight` revalidates approved scheduler activation evidence and fresh runtime env readiness before any host activation plan is prepared.

This task does not run `launchctl`, does not write to `~/Library/LaunchAgents`, and does not activate a scheduler.

## Interface

```bash
scripts/preflight_data_operations_live_scheduler_activation.sh \
  --activation-decision-report /secure/path/approve-decision-report.json \
  --env-file /secure/path/data-operations.env \
  --output-dir /secure/path/final-preflight
```

Optional explicit evidence paths:

```bash
scripts/preflight_data_operations_live_scheduler_activation.sh \
  --activation-decision-report /secure/path/approve-decision-report.json \
  --activation-request-report /secure/path/live-activation-request.json \
  --approval-gate-report /secure/path/approved-approval-gate.json \
  --operator-dry-run-report /secure/path/operator-dry-run.json \
  --env-file /secure/path/data-operations.env \
  --output-dir /secure/path/final-preflight
```

All input and output paths must be outside the repository.

## Gate Outcomes

Passing final preflight returns:

```json
{
  "final_preflight": "passed_ready_for_host_activation_plan",
  "activation_allowed_for_host_activation_plan": true,
  "host_activation_execution_allowed_in_this_task": false,
  "launchctl_executed": false
}
```

Denied user decision returns:

```json
{
  "final_preflight": "blocked_user_decision_not_approved",
  "activation_allowed_for_host_activation_plan": false
}
```

Failed runtime readiness returns:

```json
{
  "final_preflight": "blocked_runtime_env_not_ready",
  "activation_allowed_for_host_activation_plan": false
}
```

## Safety Boundary

- Activation decision, request, approval gate, operator dry-run, env file, and output dir must be outside the repository.
- Runtime env readiness is regenerated into `output-dir/evidence/fresh-runtime-env-readiness.json`.
- The env file may contain secrets, but the generated readiness and final preflight reports must remain redacted.
- Passing final preflight only allows a future host activation plan task.
- No script in this task runs `launchctl` or writes host LaunchAgents.

## Verification

Run:

```bash
bash scripts/verify_data_operations_live_scheduler_activation_final_preflight.sh
```

The verification builds the repo-outside evidence chain, validates approve and deny decision paths, regenerates runtime readiness, confirms fake secret values do not leak, refuses repo-inside paths, checks docs/roadmap markers, and runs AWH.

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

Final preflight hands off to `data-operations-live-scheduler-host-activation-plan`, which is now implemented.

Current fixed next task: `data-operations-live-scheduler-host-activation-execution-request`.

That task should request explicit approval for executing the reviewed host activation plan. Actual host mutation remains forbidden until a later explicit execution task.
