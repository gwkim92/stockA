# portfolio-and-fund-instrument-analysis-v1 Handoff

## Status

- in progress: task contract and plan are opened. This is now the immediate next task.

## Context

- `professional-coverage-refresh-after-source-remediation-v1` completed on commit `a2f2c0c`.
- SPY is currently exposed with `fund_company_financial_model_not_applicable`, which is correct but incomplete for a professional investment system.
- The existing portfolio risk budget work already has useful fund-adjacent evidence: SSGA SPY holdings import, benchmark composition coverage, active share, drift/outlier review, and position sizing review.

## Exact Next Step

- exact next step: inspect existing benchmark/portfolio DTOs and DB outputs for SPY, then design the smallest fund analysis DTO that can be rendered on `/stocks/SPY` and `/recommendations/recommendation-157` without schema or score changes if possible.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not synthesize company financials for ETF/fund-like instruments.
- Use free/public or already collected data only.
