# segment-history-source-linkage-remediation-v1 Handoff

## Status

- in progress: contract and plan are opened; EC2 source/companyfacts inspection is next.

## Context

- EC2 breadth run `1254` left ARM and EROK as `missing_source_document_linkage` or companyfacts/source blockers.
- AEIS was later resolved by `aeis-reported-segment-parser-layout-v1` and now classifies as `single_reportable_segment_no_disaggregated_segment_table` in EC2 run `1317`.
- The next gap is not parser layout. It is source truth: whether ARM/EROK have usable SEC companyfacts and raw/source documents for annual segment/financial periods.

## Exact Next Step

- exact next step: inspect ARM and EROK EC2 DB/source state, including instrument identity, SEC companyfacts availability, financial_statement_period rows, source_document linkage, and raw SEC artifact presence.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not create fake fiscal periods or fake segment rows.
- Prefer precise blocker classification over speculative data repair.
