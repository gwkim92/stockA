# sum-of-the-parts-valuation-foundation-v1 Review

## Review Status

- status: local_verified_pending_ec2

## Implemented

- Added `market.sum_of_parts_component`.
- Allowed `market.valuation_snapshot.method='sum_of_parts'`.
- Added `sum-of-parts-valuation-run` backend CLI and deterministic SQL runner.
- Added weekly cadence and `sec-filings-weekly` profile step after forecast inputs and before valuation snapshot.
- Added professional coverage expansion step so active recommendation remediation creates SOTP components before valuation snapshots.
- Extended valuation snapshot assumptions JSON with SOTP component source, component count, component rows, quality, and limitations.
- Extended frontend valuation method DTO with `sotp_evidence`.
- Updated shared valuation card to render Korean SOTP component summaries.

## Guardrails Checked

- Recommendation score weights must not change.
- Benchmark split logic must not change.
- Automatic order and broker submit must remain disabled.
- SOTP rows are evidence inputs only.

## Verification

- Passed: targeted Python tests for SOTP SQL/runner/CLI/cadence/profile/professional coverage expansion.
- Passed: targeted stock/recommendation/thesis frontend adapter contract tests.
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`.
- Passed: `cd apps/web && npm run typecheck`.
- Passed: `bash scripts/verify_migrations.sh`.
- Passed: `bash scripts/verify_project_execution_roadmap.sh`.
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task sum-of-the-parts-valuation-foundation-v1`.
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 952 tests in 5.216s`, `OK`).
- Passed: `cd apps/web && npm run build`.

## Pending

- EC2 migration, runner execution, valuation rerun, API smoke, and route smoke.
