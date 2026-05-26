# segment-history-coverage-expansion-v1 Plan

## Summary

The AAPL segment history backfill is now trend-backed and clean. The next step is to expand this from a single proof symbol to active recommendation and portfolio coverage, while making unsupported SEC segment table layouts explicit quality gaps.

## Implementation Order

1. Add a bounded coverage query for active recommendation and portfolio symbols with SEC CIK/source document availability.
2. Reuse `segment-history-backfill-run` or add a thin backend orchestration runner that iterates the bounded symbol set.
3. Persist or emit a coverage report with parsed period count, segment count, unsupported candidate count, single-period fallback count, and bad-label count.
4. Expose the coverage result through data-health or professional analysis evidence if the report is persisted.
5. EC2-smoke at least AAPL plus one additional active symbol.

## Guardrails

- No recommendation weight changes.
- No live broker submit.
- No paid provider.
- No unbounded archive crawl.
