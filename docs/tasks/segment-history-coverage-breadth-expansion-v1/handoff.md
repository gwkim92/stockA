# segment-history-coverage-breadth-expansion-v1 Handoff

## Status

- in progress: contract and plan are opened; broader EC2 coverage run is the next step.

## Context

- `segment-history-coverage-expansion-v1` proved the coverage runner works for AAPL and ADI.
- `reported-segment-parser-layout-expansion-v1` proved ADI is a single reportable segment case, not a table parser miss.
- The system now needs broader active-symbol evidence before choosing the next deterministic segment parser/data remediation target.

## Exact Next Step

- exact next step: run `segment-history-coverage-expansion-run` on EC2 with a broader target set and inspect the per-symbol `coverage_status` distribution.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not add AI extraction for financial tables before deterministic parser/data blockers are exhausted.
