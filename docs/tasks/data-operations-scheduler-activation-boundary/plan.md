# Implementation Plan

## Goal

Add the repo-local wrapper that a future scheduler can invoke safely without committing scheduler artifacts or secrets.

## Steps

1. Add `src/stockanalysis/operations/scheduler_boundary.py`.
2. Add `tests/test_data_operations_scheduler_boundary.py`.
3. Add `scripts/run_data_operations_scheduler_job.sh`.
4. Add `scripts/verify_data_operations_scheduler_activation_boundary.sh`.
5. Add docs and update roadmap/README/verification/AGENTS.
6. Run targeted and full verification.

## Boundary

- Scheduler calls the wrapper with `--env-file`, `--job-id`, optional `--run-date`, optional `--skip-dates`, and command after `--`.
- Wrapper refuses repo-inside env files.
- Wrapper runs `scripts/check_data_operations_runtime_env.sh` first.
- Wrapper sources the trusted env and calls `stockanalysis-ingest data-operations-run`.
- `--preflight-only` emits a JSON contract without executing the child command.
- Skip-date hit emits a JSON skip artifact and exits 0 without running the child command.

## Security

- Env values are never printed.
- Command argv is redacted in preflight.
- Artifact runner metadata redacts sensitive args.
- This task creates no host scheduler files.
