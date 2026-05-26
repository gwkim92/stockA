# aeis-reported-segment-parser-layout-v1 Handoff

## Status

- in progress: contract and plan are opened; AEIS raw SEC artifact inspection is next.

## Context

- Breadth run `1254` selected `AAPL/ADI/AEIS/ALAB/ARM/DIS/ELF/EROK/FANG/GILD`.
- Status counts were `trend_backed=4`, `single_reportable_segment_no_disaggregated_segment_table=3`, `unsupported_layout=1`, and `missing_source_document_linkage=2`.
- AEIS is the only current true unsupported parser/layout blocker in that run.

## Exact Next Step

- exact next step: inspect AEIS raw SEC artifacts under `/opt/stockanalysis/runtime/artifacts/raw` on EC2, identify the segment table shape, and add deterministic parser support or a precise skip reason.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Preserve AAPL and ADI classifications.
