# aeis-reported-segment-parser-layout-v1 Handoff

## Status

- completed: AEIS raw SEC artifact inspection showed a single reporting segment disclosure rather than a missing parser layout.

## Context

- Breadth run `1254` selected `AAPL/ADI/AEIS/ALAB/ARM/DIS/ELF/EROK/FANG/GILD`.
- Status counts were `trend_backed=4`, `single_reportable_segment_no_disaggregated_segment_table=3`, `unsupported_layout=1`, and `missing_source_document_linkage=2`.
- AEIS 2025/2024 10-K raw artifacts state that management operates in a single reporting segment, power electronics conversion products.
- The implementation now recognizes company-specific `single reporting segment` statements while ignoring ASU/FASB accounting-standard-only mentions.
- EC2 bounded coverage smoke `run_id=1317` selected AAPL/ADI/AEIS and reported `unsupported_layout_count=0`; AAPL stayed `trend_backed`, ADI stayed `single_reportable_segment_no_disaggregated_segment_table`, and AEIS moved to `single_reportable_segment_no_disaggregated_segment_table`.

## Exact Next Step

- exact next step: continue with `segment-history-source-linkage-remediation-v1` for ARM/EROK source/companyfacts blockers.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Preserve AAPL and ADI classifications.
