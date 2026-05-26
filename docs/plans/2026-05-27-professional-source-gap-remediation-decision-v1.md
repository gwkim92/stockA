# professional-source-gap-remediation-decision-v1 Plan

## Summary

The source-gap ranking is now live on EC2. The next value is not another UI layer; it is deciding what to do with the top ranked gaps without fabricating financial facts or changing recommendation weights.

## Implementation Order

1. Query live `/api/data-health` and capture the ranked source-gap list.
2. Inspect the top true source blocker (`EROK`) and determine whether current free public data can remediate it.
3. If non-remediable, record the blocker as explicit and keep it excluded from company-financial coverage.
4. Move to the next deterministic remediable coverage gap (`GOOG` if still ranked) and run the existing backend remediation command only if it is safe.
5. Refresh data-health and verify the ranked list, order boundary, and weight mutation flags.

## Guardrails

- No recommendation weight changes.
- No synthetic financial data.
- No paid provider requirement.
- No broker/order submit.
