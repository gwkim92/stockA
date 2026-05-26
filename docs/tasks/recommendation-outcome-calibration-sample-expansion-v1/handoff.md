# recommendation-outcome-calibration-sample-expansion-v1 Handoff

## Status

- pending: this is the immediate next task after `fund-tracking-error-source-v1`.

## Context

- Professional analysis evidence now exists for company financials, valuation, SOTP, thesis lifecycle, portfolio risk, position sizing, and ETF/fund source metrics.
- Recommendation weights remain intentionally unchanged because outcome evidence is still too sparse for a defensible calibration change.
- The next useful move toward the project goal is not another UI label pass. It is outcome/calibration evidence that can prove whether the professional components improve medium-long recommendation quality.

## Exact Next Step

- exact next step: inspect current performance/eval schema and latest EC2 recommendation quality reports to determine which outcome horizons, symbols, and missing reasons are under-covered.

## Guardrails

- Keep all recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not fabricate outcomes for missing price history.
- Do not change benchmark splits without explicit approval.
