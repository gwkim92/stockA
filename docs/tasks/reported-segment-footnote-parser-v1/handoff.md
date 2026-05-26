# reported-segment-footnote-parser-v1 Handoff

## Status

- completed locally: implementation, task docs, roadmap update, and local verification are complete.
- pending: optional EC2 deployment/smoke.

## Current Findings

- `research.segment_footnote_evidence` already supports `reported_segment_metric`; no migration is required.
- Previous `segment-footnote-evidence-run` only produced filing anchors, consolidated metrics, and explicit segment data gap rows.
- SEC companyfacts period rows can link to `ingest.source_document` through accession number when matching SEC filing documents exist.
- The parser currently supports local `file://` raw SEC filing artifacts and simple HTML segment tables. Unsupported raw URIs are skipped and reported rather than failing the job.

## Decisions

- Implement deterministic parsing inside the `stockanalysis-operations` backend boundary, not as shell orchestration.
- Keep extracted segment metrics as evidence only. SOTP can see `reported_segment_metric_count`, but recommendation score/weight and valuation math are not changed in this task.
- Delete same-date `segment_data_gap` rows only for instruments/periods where reported segment metrics were parsed, so the UI stops showing a false gap for those rows.
- Keep the parser conservative: no complete inline XBRL taxonomy parser is claimed.

## Exact Next Step

- exact next step: run the full verification commands from the contract, then deploy/smoke on EC2 if local verification stays clean.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_professional_equity_analysis tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator tests.test_professional_coverage_expansion` (`Ran 120 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "reported-segment-footnote-parser-run|segment-footnote-evidence-run"`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task reported-segment-footnote-parser-v1`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 964 tests in 5.195s`, `OK`)
- Passed: `git diff --check`
- Not accepted as code failure: `PYTHONPATH=src python3 -m unittest discover -s tests` failed under Homebrew Python 3.14 because that interpreter has the known local `pyexpat` dynamic-link issue and lacks `fastapi`; the same full suite passed under the project verification Python 3.13 venv.

## Remaining Risks

- Real SEC filings often have complex inline XBRL tables, nested headers, or dimensional facts; this first parser only covers straightforward HTML segment tables.
- EC2 may still have few or zero parser candidates if `market.financial_statement_period.source_document_id` is missing for covered instruments.
- Broader source-document linkage and richer SEC taxonomy parsing remain future work.
