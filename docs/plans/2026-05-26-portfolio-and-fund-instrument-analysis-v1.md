# portfolio-and-fund-instrument-analysis-v1 Plan

## Summary

SPY and similar ETF/fund-like instruments should not be analyzed as operating companies. The system now labels SPY as `fund_company_financial_model_not_applicable`; this task turns that blocker into a useful professional analysis lane based on holdings, benchmark composition, tracking/drift proxy, expense/liquidity availability, exposure, and portfolio role.

## Implementation Order

1. Inspect existing portfolio/benchmark/holding DTOs and DB evidence for SPY.
2. Define a read-only fund analysis payload for stock and recommendation detail.
3. Reuse existing benchmark composition, holdings coverage, drift, active share, concentration, and position sizing evidence before adding schema.
4. Render fund analysis on `/stocks/[symbol]` and `/recommendations/[id]` when `source_data_blocker.blocker_code` is `fund_company_financial_model_not_applicable`.
5. Keep missing expense ratio, tracking error, and liquidity fields explicit as unknown/null if no free source is already present.
6. Verify SPY route output and recommendation detail in EC2 without score/order changes.

## Guardrails

- No recommendation weight changes.
- No live broker submit.
- No paid provider.
- No fake company financial statement rows for ETFs/funds.
- No exact tracking-error claim unless supported by collected data.

## Completion Evidence

- Implemented in commits `f16e757` and `ea9a0dc`.
- EC2 API smoke confirms SPY fund analysis uses `ssga_spdr_spy_daily_holdings`, 503 holdings, coverage `0.9983782`, top holdings `NVDA/AAPL/MSFT/AMZN/GOOGL`, and read-only order boundary.
- `/stocks/SPY` and `/recommendations/recommendation-157` render ETF/fund analysis panels. Tracking error and expense ratio remain explicit `not_collected` states for the next task.
