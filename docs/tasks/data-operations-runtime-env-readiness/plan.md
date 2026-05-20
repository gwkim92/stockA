# Implementation Plan

## Goal

Create a repo-local activation gate for data operations runtime env readiness without committing credentials or activating schedulers.

## Steps

1. Add `src/stockanalysis/operations/env_readiness.py`.
2. Add unit tests for passing env, missing groups, placeholder values, repo-inside paths, invalid DB boundary, and secret-free output.
3. Add `stockanalysis-ingest data-operations-env-readiness` CLI.
4. Add scripts to render a repo-outside env template and check a trusted repo-outside env file.
5. Add `scripts/verify_data_operations_runtime_env_readiness.sh`.
6. Add operator documentation and update roadmap/README/verification/handoff.
7. Run targeted and full verification.

## Design

- Validate groups: `database`, `fred`, `alpha_vantage`, `sec_identity`, `portfolio_snapshot_source`, `openai_or_llm_provider`, `artifact_root`.
- Accept database readiness through either `STOCKANALYSIS_DATABASE_URL` or `STOCKANALYSIS_PSQL_COMMAND`.
- Require `STOCKANALYSIS_PORTFOLIO_POSITIONS_CSV` to be an existing absolute file.
- Require `STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT` to be absolute, writable, and outside the repository.
- Require `STOCKANALYSIS_LLM_PROVIDER`; for provider `openai`, require `OPENAI_API_KEY`.
- Never echo raw secrets or database URLs. Public JSON exposes only booleans, env variable names, provider name, path labels, and non-secret command argv0.

## Verification

- `bash scripts/verify_data_operations_runtime_env_readiness.sh`
- `bash scripts/verify_data_operations_artifact_runner.sh`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=src python3 -m unittest discover -s tests`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task data-operations-runtime-env-readiness`
- `git diff --check`
