# cycle-ai-quality-audit-contamination-remediation-v1 Plan

## Summary

The system now has working news automation again, but AI/news quality is still not trustworthy enough for recommendation input. The next step is to reduce contamination in `cycle_ai_quality_audit` without changing recommendation weights or hiding warnings.

## Implementation Order

1. Inspect latest EC2 `cycle_ai_quality_audit` payload and sample rows.
2. Pick one issue class with the clearest root cause.
3. Trace from data-health sample to source event, AI artifact, validator, and canonical impact rows.
4. Add a deterministic validator/dedupe/reclassification fix.
5. Add focused tests.
6. Rerun EC2 `cycle-ai-quality-audit-run --execute`.
7. Confirm `/api/data-health` shows reduced or more accurate issue counts.

## Guardrails

- No recommendation weight changes.
- No broker/order enablement.
- No paid provider requirement.
- No warning suppression without evidence.
