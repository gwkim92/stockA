# financial-period-source-document-linkage-v1 Handoff

## Status

- completed: backend runner, CLI, cadence/profile integration, local verification, roadmap verification, harness verification, GitHub push, EC2 deploy, and EC2 linkage/parser smoke are complete.

## Current Findings

- `reported-segment-footnote-parser-v1` works as a bounded parser, but EC2 produced zero candidates because no financial statement periods were linked to SEC source documents and no linked raw SEC filing artifacts existed.
- `sec_companyfacts_upsert` can link period rows to source documents by accession number when matching `sec_filings_upsert` source documents already exist.
- Older EC2 data can remain unlinked if companyfacts ran before filings or if existing periods were created without matching source documents.
- First EC2 linkage smoke with `--max-filings 3` succeeded as a run but linked zero periods because the latest three Apple filings were Form 4/144, not 10-K/10-Q. Source linkage therefore uses a wider bounded default lookback of 200 filings while the normal lightweight SEC filings step stays at 3.

## Decisions

- Add `financial-period-source-linkage-run` inside the `stockanalysis-operations` backend boundary rather than adding another shell script.
- In execute mode, refresh SEC filings metadata, rerun SEC companyfacts for the same CIK, run a deterministic SQL backfill for still-unlinked periods, then raw-fetch a bounded number of linked SEC documents.
- Keep the operation preview-first and bounded by `--max-filings` and `--raw-fetch-limit`.
- Do not change recommendation scores, component weights, benchmark/evaluation split, or broker/order flow.

## Exact Next Step

- exact next step: start `reported-segment-parser-quality-v1` to expand parsing coverage for real linked SEC raw filings, because EC2 now has a parser candidate but the current simple parser extracted zero metrics from Apple 10-K.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_financial_period_source_linkage tests.test_data_operations_cli tests.test_data_operations_cadence tests.test_operating_data_orchestrator` (`Ran 88 tests`, `OK`)
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help | rg "financial-period-source-linkage-run|reported-segment-footnote-parser-run"`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task financial-period-source-document-linkage-v1`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 970 tests in 5.221s`, `OK`)
- Passed: `git diff --check`
- Re-passed after source-linkage lookback correction: focused unittest (`Ran 88 tests`, `OK`), `compileall`, roadmap verification, AWH verify, CLI help grep, Python 3.13 full suite (`Ran 970 tests in 5.227s`, `OK`), and `git diff --check`.
- EC2 first smoke: `financial-period-source-linkage-run --max-filings 3 --execute` completed with `run_id=1039`, `linked_period_count=0`, `raw_fetch_candidate_count=0`; root cause was insufficient filing lookback.
- Pushed: `9a97393 Add financial period source linkage` and `a2b45f8 Widen SEC source linkage lookback` to `origin/codex/local-mvp-runtime-aws-bootstrap`.
- EC2 deployed: `/opt/stockanalysis/app` fast-forwarded to `a2b45f8`.
- EC2 linkage smoke passed: `financial-period-source-linkage-run --max-filings 200 --execute` completed with `run_id=1042`, `sec_filings_report.filing_count=200`, `raw_fetch_candidate_count=1`, `raw_fetch_success_count=1`, and raw Apple 10-K artifact `file:///opt/stockanalysis/runtime/artifacts/raw/sec/filings/0000320193-25-000079/aapl-20250927.htm`.
- EC2 DB linkage check passed: `total_periods=2696`, `linked_periods=29`, `raw_sec_docs=1`, `linked_raw_periods=2`, `aapl_periods=195`, `aapl_linked_periods=29`.
- EC2 parser candidate smoke passed: `reported-segment-footnote-parser-run --execute` completed with `run_id=1046`, `candidate_count=1`, `reported_segment_metric_count=0`, `recommendation_scoring_mutated=false`.
- EC2 services remained active: `stockanalysis-frontend-api.service` and `stockanalysis-web.service`.

## Remaining Risks

- The deterministic backfill relies on accession-number linkage first and conservative filing-date/company-text matching second; unusual issuer names or filings may remain unlinked.
- `--raw-fetch-limit` intentionally prevents unlimited SEC downloads, so full coverage requires repeated scheduled runs.
- This task unblocks parser input availability; it does not make the parser itself a full inline XBRL taxonomy engine.
- The first real linked Apple 10-K candidate produced zero parsed metrics, so parser coverage/depth is the next blocker for segment-level SOTP quality.
