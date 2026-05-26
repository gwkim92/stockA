# reported-segment-parser-layout-expansion-v1 Handoff

## Status

- in progress: contract and plan are opened; ADI raw SEC artifact inspection and parser fixture work are next.

## Context

- `segment-history-coverage-expansion-v1` completed on EC2 with parent `run_id=1134`.
- AAPL is clean and trend-backed.
- ADI now has source/raw annual document coverage but `coverage_status=unsupported_layout`, with `source_document_period_count=3`, `raw_document_period_count=3`, `parsed_period_count=0`, and `unsupported_candidate_count=3`.

## Exact Next Step

- exact next step: inspect the ADI raw SEC artifacts under `/opt/stockanalysis/runtime/artifacts/raw` on EC2, extract the segment table shape, and add a deterministic parser fixture/test for that layout.

## Guardrails

- Preserve AAPL bad-label filters.
- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
