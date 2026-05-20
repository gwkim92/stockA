# Data Operations Backend Orchestration Boundary

## Summary

This slice corrects the data operations boundary before continuing host scheduler activation final preflight.

The project already has backend code, but some data operations host activation wrappers were carrying backend concerns in shell: argument validation, repo-outside path enforcement, JSON report IO, and Python heredoc dispatch. This task moves the first representative path into `src/stockanalysis/operations/` and adds a `stockanalysis-operations` console entrypoint.

## Decision

- FastAPI remains the read-only frontend DTO API.
- Data operations orchestration belongs in the Python operations backend package.
- Shell remains valid for `scripts/verify_*.sh` and thin compatibility wrappers.
- `stockanalysis-ingest data-operations-*` remains available for compatibility.
- New backend operations entrypoint is `stockanalysis-operations`.

## Implemented First Slice

- Added `src/stockanalysis/operations/cli.py`.
- Added `src/stockanalysis/operations/path_policy.py`.
- Added `src/stockanalysis/operations/report_io.py`.
- Added `stockanalysis-operations` console script.
- Converted `scripts/decide_data_operations_live_scheduler_host_activation_execution.sh` to a thin wrapper.
- Added CLI/path policy tests.

## Guardrails

- No `launchctl` execution.
- No host LaunchAgents writes.
- No FastAPI write endpoints.
- No DB schema changes.
- No broker/order flow.

## Follow-up

Next scheduler activation work should use `stockanalysis-operations` rather than adding more shell-owned orchestration. Remaining non-verify wrappers should be migrated incrementally.
