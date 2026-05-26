# segment-history-source-linkage-remediation-v1 Handoff

## Status

- in progress: ARM has been remediated through 20-F companyfacts support and parser cleanup; EROK remains to be classified as a precise no-financial-facts/new-listing blocker.

## Context

- EC2 breadth run `1254` left ARM and EROK as `missing_source_document_linkage` or companyfacts/source blockers.
- AEIS was later resolved by `aeis-reported-segment-parser-layout-v1` and now classifies as `single_reportable_segment_no_disaggregated_segment_table` in EC2 run `1317`.
- The next gap is not parser layout. It is source truth: whether ARM/EROK have usable SEC companyfacts and raw/source documents for annual segment/financial periods.
- ARM SEC companyfacts has `us-gaap` facts, but the financial reports are Form `20-F`; the previous normalizer only accepted `10-K` and `10-Q`, so ARM had no periods.
- ARM now accepts `20-F` as audited annual companyfacts. EC2 source linkage `run_id=1339` created ARM periods from 54 facts across 8 periods and raw-fetched 2 filings.
- ARM also exposed parser contamination: old logic treated `Operating expenses` and `Non-staff costs` as reported segments. The parser now skips single operating segment financial summary tables, excludes expense/financial statement labels, and removes stale reported segment rows for skipped candidates.
- EC2 coverage smoke `run_id=1416` selected AAPL/ADI/AEIS/ALAB/ARM and reported AAPL `trend_backed`, ADI/AEIS/ALAB/ARM `single_reportable_segment_no_disaggregated_segment_table`, `unsupported_layout_count=0`, `arm_reported_segment_metric_count=0`, and read-only score/order guardrails.
- EROK SEC companyfacts currently exposes only `ffd` taxonomy samples and no `us-gaap` financial facts, while SEC recent filings are S-8/8-K/ownership/certification rather than annual financial statements.

## Exact Next Step

- exact next step: implement a deterministic EROK blocker classification for `sec_companyfacts_no_financial_statement_facts` or equivalent, then re-run the 10-symbol breadth coverage to prove ARM stays clean and EROK is no longer ambiguous.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not create fake fiscal periods or fake segment rows.
- Prefer precise blocker classification over speculative data repair.
