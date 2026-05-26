# professional-coverage-refresh-after-source-remediation-v1 Plan

## Summary

The segment/source remediation sequence removed generic unsupported parser states from the active 10-symbol sample and replaced EROK with a precise SEC companyfacts source blocker. The next step is not another parser change; it is to refresh downstream professional analysis evidence so the stock and recommendation experience reflects the cleaned source truth.

## Implementation Order

1. Run or inspect the latest EC2 professional coverage expansion after source cleanup.
2. Check stock/recommendation DTOs for symbols affected by remediation, especially ARM and EROK.
3. Confirm no polluted ARM segment labels remain in SOTP, valuation, or recommendation evidence.
4. Confirm EROK is shown as source-data unavailable rather than parser failure where applicable.
5. Patch backend DTO/frontend wording only if stale or misleading evidence is still exposed.

## Guardrails

- No recommendation weight changes.
- No live broker submit.
- No paid provider.
- No synthetic segment rows for single-segment companies.

## Completion Evidence

- EC2 coverage refresh `run_id=1519`, post-decision refresh `run_id=1565`, recommendation component rerun `run_id=1579`, and quality eval `run_id=1580`/`eval_run_id=25` completed the bounded refresh.
- Source blockers are now visible in API/frontend: SPY is `fund_company_financial_model_not_applicable`, EROK is `sec_companyfacts_missing_us_gaap_facts`, and ARM remains financial-model available without polluted segment labels.
- Recommendation weights and broker/order flow stayed unchanged.
