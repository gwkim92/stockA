# segment-history-source-linkage-remediation-v1 Plan

## Summary

`aeis-reported-segment-parser-layout-v1` removed the last generic unsupported segment parser layout from the active breadth sample. The remaining breadth blockers are ARM and EROK, which failed before parser support because source/companyfacts linkage was missing or unsupported. This task investigates those source truth blockers and either remediates them through existing SEC/source linkage paths or records precise deterministic blockers.

## Implementation Order

1. Inspect ARM and EROK source state on EC2: instrument identity, SEC companyfacts response shape, `market.financial_statement_period`, `ingest.source_document`, and raw SEC artifacts.
2. Determine whether each symbol is a supported operating company with missing linkage, an unsupported security/companyfacts shape, or a data provider gap.
3. Add deterministic classification or remediation in the relevant backend service boundary.
4. Add focused unit tests for the observed blocker or remediation path.
5. Re-run bounded coverage for ARM/EROK plus one known-good control and verify score/order guardrails remain read-only.

## Guardrails

- No recommendation weight changes.
- No live broker submit.
- No paid provider.
- No fake source documents or inferred segment rows.
