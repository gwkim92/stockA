# sum-of-the-parts-valuation-foundation-v1 Review

## Review Status

- status: completed_ec2_verified

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

- Next task should replace proxy SOTP components with stronger segment-level evidence where SEC footnote/business segment data is available.

## EC2 Verification

- Passed: commit `788ade2` was pushed and fast-forwarded on EC2.
- Passed: EC2 migration created `market.sum_of_parts_component` and allowed `sum_of_parts` valuation snapshots.
- Passed: EC2 `sum-of-parts-valuation-run` for `2026-05-26` completed with `run_id=1031`, `component_row_count=45`, and component type counts `operating_business=16`, `balance_sheet_adjustment=12`, `risk_reserve=17`.
- Passed: EC2 `valuation-snapshot-run` for `2026-05-26` completed with `run_id=1032`, `snapshot_count=68`, and `sum_of_parts=16`.
- Passed: EC2 temporal smoke for `recommendation-151` used matching recommendation date `2026-05-25`; SOTP `run_id=1033` and valuation `run_id=1034` completed.
- Passed: `/api/stocks/NVDA`, `/api/recommendations/recommendation-151`, and `/api/theses/thesis-5` expose `sum_of_parts` with `sotp_evidence.status=available`, component count `3`, and first component `operating_business_fcf`.
- Passed: `/stocks/NVDA`, `/recommendations/recommendation-151`, and `/theses/thesis-5` render `SOTP 구성요소`, `영업사업 가치`, `세그먼트 데이터 공백`, and `재무 forecast 입력`.
