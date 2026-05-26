# professional-source-blocker-raw-filing-remediation-v1 Plan

## Summary

After GOOG remediation, the remaining true professional source blocker is EROK. The next task is not another UI layer. It is deciding whether free public raw filing/XBRL data can safely support EROK financial analysis, and if not, making the exclusion durable and visible.

## Implementation Order

1. Inspect EROK SEC identity, CIK, available filings, and companyfacts payload shape.
2. Determine whether raw SEC filing/XBRL or another free public source provides usable revenue, cash flow, assets/liabilities, and share count.
3. If usable, implement a backend source parser/runner that writes canonical financial/source evidence through existing service boundaries.
4. If not usable, write a durable blocker/exclusion artifact so EROK is no longer treated as a remediable coverage gap.
5. Refresh `/api/data-health`, `/data-health`, and affected stock/recommendation surfaces.

## Guardrails

- No synthetic financial facts.
- No recommendation weight changes.
- No paid provider requirement.
- No broker/order submit.
