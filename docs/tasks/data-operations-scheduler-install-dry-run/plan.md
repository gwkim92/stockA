# Implementation Plan

## Goal

Render the data operations host scheduler artifact in dry-run mode without installing or activating it.

## Steps

1. Add `src/stockanalysis/operations/scheduler_install.py`.
2. Add `tests/test_data_operations_scheduler_install.py`.
3. Add `scripts/render_data_operations_scheduler_install.sh`.
4. Add `scripts/verify_data_operations_scheduler_install_dry_run.sh`.
5. Add docs and update roadmap/README/verification/AGENTS.
6. Run targeted and full verification.

## Boundary

- Renderer writes only to caller-provided repo-outside output dir.
- Renderer refuses env files inside the repository.
- Rendered launchd plist calls `scripts/run_data_operations_scheduler_job.sh`.
- Renderer supports daily and weekly launchd schedules derived from cadence `expected_after_local`.
- Monthly `first-business-day` jobs are rejected because launchd cannot express that safely without a separate calendar wrapper.

## Security

- Env values are never read or printed by the renderer.
- Manifest exposes path and schedule metadata only.
- No file is written to `~/Library/LaunchAgents`.
