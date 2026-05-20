# Data Operations Live Scheduler Host Activation Execution Final Preflight

Date: 2026-05-11

## Decision

`data-operations-live-scheduler-host-activation-execution-final-preflight` revalidates approved host activation execution evidence immediately before any separate host mutation task.

This task does not run `launchctl`, does not write `~/Library/LaunchAgents`, and does not execute child data operation commands.

## Interface

```bash
scripts/preflight_data_operations_live_scheduler_host_activation_execution.sh \
  --execution-decision-report /secure/path/approve-execution-decision-report.json \
  --env-file /secure/path/data-operations.env \
  --output-dir /secure/path/execution-final-preflight
```

Optional inputs:

- `--execution-request-report PATH`
- `--host-activation-plan-report PATH`

If omitted, those paths are read from upstream evidence.

## Pass Outcome

Approved execution decision plus fresh runtime readiness returns:

```json
{
  "execution_final_preflight": "passed_ready_for_host_activation_execution_task",
  "host_activation_execution_allowed_for_next_task": true,
  "host_activation_execution_allowed_in_this_task": false,
  "launchctl_executed": false,
  "host_install_path_written": false
}
```

## Block Outcomes

- `blocked_execution_decision_not_approved`
- `blocked_runtime_env_not_ready`

The preflight also rejects command preview drift between the reviewed host activation plan and execution request.

## Safety Boundary

- All input and output paths must be outside the repository.
- Runtime env values are loaded and checked in Python, then reported with values redacted.
- Command previews may mention `install` and `launchctl`, but this task must not execute them.
- Passing this preflight only allows a future execution task.
- Raw env values, DB URLs, API keys, bearer tokens, and passwords are rejected from report metadata.

## Verification

Run:

```bash
bash scripts/verify_data_operations_live_scheduler_host_activation_execution_final_preflight.sh
```

The verification builds a repo-outside evidence chain through execution decision, runs final preflight, confirms fake secret values do not leak, refuses repo-inside paths and drifted evidence, checks docs/roadmap markers, and runs AWH.

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

This task hands off to a separate `data-operations-live-scheduler-host-activation-execution` task. That future task is high-risk host mutation and must not execute without explicit user confirmation.
