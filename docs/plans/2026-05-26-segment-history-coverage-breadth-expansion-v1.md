# segment-history-coverage-breadth-expansion-v1 Plan

## Summary

`reported-segment-parser-layout-expansion-v1` proved ADI is a single reportable segment case rather than a generic parser failure. The next step is to broaden the coverage run beyond AAPL and ADI so active recommendations and portfolio holdings have explicit segment history statuses.

## Implementation Order

1. Run `segment-history-coverage-expansion-run` with a broader active-symbol target set.
2. Classify symbols into trend-backed, single reportable segment, missing source linkage, missing raw SEC artifact, contaminated labels, single-period fallback, and true unsupported parser layout.
3. Rank remaining blockers by investment relevance and fix deterministic parser/data issues before adding AI extraction.
4. Record EC2 evidence and update the roadmap with the next precise remediation target.

## Guardrails

- No recommendation weight changes.
- No live broker submit.
- No paid provider.
- Keep all work inside `stockanalysis-operations` service boundaries.
