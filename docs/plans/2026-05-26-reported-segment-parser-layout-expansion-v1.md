# reported-segment-parser-layout-expansion-v1 Plan

## Summary

The coverage expansion runner proved that ADI now has linked/raw annual SEC documents but the current reported segment parser cannot parse its segment table layout. The next task is to add deterministic parser coverage for that observed layout without weakening AAPL safeguards.

## Implementation Order

1. Locate ADI raw annual filing artifacts from EC2 run `1134`.
2. Capture the relevant segment table snippet as a local fixture.
3. Add a parser function or extend an existing parser path for the observed layout.
4. Add unit tests proving ADI-like rows parse and AAPL bad-label filters still hold.
5. EC2 rerun `segment-history-coverage-expansion-run` for AAPL + ADI.

## Guardrails

- No score weight changes.
- No live broker submit.
- No paid provider.
- No prompt-only AI parser for financial tables.
