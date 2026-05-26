# aeis-reported-segment-parser-layout-v1 Plan

## Summary

`segment-history-coverage-breadth-expansion-v1` identified AEIS as the first remaining true `unsupported_layout` among the broader active-symbol segment coverage run. ADI/ALAB/ELF are single reportable segment cases, while ARM/EROK are source/companyfacts blockers. AEIS has raw/source annual filings and mixed skip reasons, so it is the next deterministic parser target.

## Implementation Order

1. Inspect AEIS raw SEC artifacts from EC2 run `1254`.
2. Extract the relevant segment or disaggregation table shape into a local fixture.
3. Add deterministic parser support if the table contains reported segment revenue/income by business segment.
4. If the filing does not contain usable operating segment data, classify it with a more specific blocker rather than generic `unsupported_layout`.
5. Re-run coverage for AAPL, AEIS, and ADI to prove AAPL remains clean, ADI remains single-segment, and AEIS improves.

## Guardrails

- No recommendation weight changes.
- No live broker submit.
- No paid provider.
- No AI extraction of financial tables before deterministic evidence is exhausted.
