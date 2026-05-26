# portfolio-attribution-monthly-profile-integration-v1 Contract

## Task Request

- request: Fix the missing monthly portfolio attribution operating-data gate so performance attribution is not only an expected data-health job but an actual scheduled profile step.
- context: `/data-health` reports `portfolio-attribution-monthly` as missing because `DATA_OPERATION_CADENCES` defines the job, but `performance-monthly` does not run an attribution step. EC2 currently has `performance.thesis_outcome` rows and portfolio snapshots, but `performance.attribution_run` count is zero.

## Goal

- goal: Add a `stockanalysis-operations` portfolio attribution runner and include it in `performance-monthly` after outcome backfill so monthly performance validation can create or no-op-record attribution evidence.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/portfolio_attribution.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `tests/`
  - `docs/project-execution-roadmap.md`
  - `AGENTS.md`
  - `docs/tasks/portfolio-attribution-monthly-profile-integration-v1/*`

## Invariants

- No recommendation score weight changes.
- No broker submit, order write API, or live trading path.
- No schema or benchmark definition changes.
- Attribution is a performance measurement artifact only; it must not mutate recommendations, theses, positions, or portfolio allocation decisions.
- New data operations entrypoints must use `stockanalysis-operations` CLI/service boundary rather than adding shell orchestration.

## Scope

- Add an operations runner that selects the latest eligible `(snapshot_date, measurement_end_date)` attribution window on or before `--as-of-date`.
- If an eligible window exists, call the existing deterministic `run_portfolio_attribution_bootstrap`.
- If no eligible window exists, record a successful no-op `ops.pipeline_run` with explicit reason so `/data-health` is not falsely missing.
- Add `portfolio-attribution-monthly` to the `performance-monthly` profile after `performance-outcome-monthly`.
- Update cadence command metadata to use `stockanalysis-operations portfolio-attribution-run`.

## Verification

- verification command: focused tests for the new runner, CLI wiring, cadence, and orchestrator profile.
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck && npm run build`
- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
- verification command: `bash scripts/verify_project_execution_roadmap.sh`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-attribution-monthly-profile-integration-v1`
