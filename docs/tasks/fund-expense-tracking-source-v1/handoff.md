# fund-expense-tracking-source-v1 Handoff

## Status

- in progress: task contract and plan are opened. This is now the immediate next task.

## Context

- `portfolio-and-fund-instrument-analysis-v1` completed on commit `ea9a0dc`.
- SPY fund analysis currently has high-quality holdings evidence from `ssga_spdr_spy_daily_holdings`.
- Expense ratio and tracking error are intentionally `not_collected`; they must not be guessed.

## Exact Next Step

- exact next step: inspect current collected market/benchmark/provider artifacts for NAV, premium/discount, volume/liquidity, and expense ratio fields before deciding whether a schema or runner is needed.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Use free/public or already collected data only.
- Preserve explicit unknown states when no auditable source exists.
