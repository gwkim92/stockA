# segment-footnote-extraction-foundation-v1 Handoff

## Status

- completed: schema, runner, CLI, operations integration, SOTP assumptions, DTO/UI, and local verification are complete.
- in progress: EC2 deployment/smoke is still pending.

## Current Findings

- `market.sum_of_parts_component` exists and SOTP valuation snapshots are available.
- Existing SOTP component math is deliberately conservative proxy logic.
- SEC companyfacts ingestion links `market.financial_statement_period.source_document_id` to `ingest.source_document` when filing accession documents exist.
- `research.segment_footnote_evidence` now stores filing anchors, consolidated metric evidence, reserved `reported_segment_metric` rows, and explicit `segment_data_gap` rows.
- SOTP valuation assumptions now carry segment evidence metadata so users can see whether SOTP has true segment data or only consolidated/gap evidence.

## Decisions

- Add `research.segment_footnote_evidence` because the first layer is research evidence, not a direct market model.
- Do not pretend consolidated financial statement metrics are reported business segments.
- Generate explicit `segment_data_gap` rows to show where future segment-level extraction is still missing.
- Keep recommendation scores, score weights, benchmark, and broker/order flow unchanged.

## Exact Next Step

- exact next step: deploy to EC2, run `segment-footnote-evidence-run`, rerun SOTP and valuation snapshots, and smoke `/api/stocks/NVDA` plus stock/recommendation/thesis routes.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_stock_detail_response_matches_frontend_contract_shape`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `bash scripts/verify_migrations.sh` applied through `0026_segment_footnote_evidence.sql` and created `research.segment_footnote_evidence`.
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "segment-footnote-evidence-run|sum-of-parts-valuation-run"`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task segment-footnote-extraction-foundation-v1`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 958 tests in 5.184s`, `OK`)

## Remaining Risks

- This foundation does not yet parse full SEC HTML/XBRL segment footnotes.
- True segment-level SOTP still requires `reported-segment-footnote-parser-v1`.
- EC2 smoke has not been recorded yet for this task.
