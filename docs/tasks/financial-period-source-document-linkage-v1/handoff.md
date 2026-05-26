# financial-period-source-document-linkage-v1 Handoff

## Status

- in progress: backend runner, CLI, cadence/profile integration, local verification, roadmap verification, and harness verification are complete.
- remaining: GitHub push, EC2 deploy, and EC2 linkage/parser smoke.

## Current Findings

- `reported-segment-footnote-parser-v1` works as a bounded parser, but EC2 produced zero candidates because no financial statement periods were linked to SEC source documents and no linked raw SEC filing artifacts existed.
- `sec_companyfacts_upsert` can link period rows to source documents by accession number when matching `sec_filings_upsert` source documents already exist.
- Older EC2 data can remain unlinked if companyfacts ran before filings or if existing periods were created without matching source documents.

## Decisions

- Add `financial-period-source-linkage-run` inside the `stockanalysis-operations` backend boundary rather than adding another shell script.
- In execute mode, refresh SEC filings metadata, rerun SEC companyfacts for the same CIK, run a deterministic SQL backfill for still-unlinked periods, then raw-fetch a bounded number of linked SEC documents.
- Keep the operation preview-first and bounded by `--max-filings` and `--raw-fetch-limit`.
- Do not change recommendation scores, component weights, benchmark/evaluation split, or broker/order flow.

## Exact Next Step

- exact next step: run the contract verification commands, push the implementation, deploy to EC2, then execute `financial-period-source-linkage-run` followed by `reported-segment-footnote-parser-run` to confirm parser candidates are unblocked.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_financial_period_source_linkage tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator` (`Ran 88 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "financial-period-source-linkage-run|reported-segment-footnote-parser-run"`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task financial-period-source-document-linkage-v1`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 970 tests in 5.221s`, `OK`)
- Passed: `git diff --check`

## Remaining Risks

- The deterministic backfill relies on accession-number linkage first and conservative filing-date/company-text matching second; unusual issuer names or filings may remain unlinked.
- `--raw-fetch-limit` intentionally prevents unlimited SEC downloads, so full coverage requires repeated scheduled runs.
- This task unblocks parser input availability; it does not make the parser itself a full inline XBRL taxonomy engine.
