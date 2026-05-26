# portfolio-and-fund-instrument-analysis-v1 Handoff

## Status

- completed: stock and recommendation DTOs expose `fund_instrument_analysis`; SPY routes render holdings-based ETF/fund analysis; EC2 API and route smoke are complete.

## Context

- `professional-coverage-refresh-after-source-remediation-v1` completed on commit `a2f2c0c`.
- SPY is currently exposed with `fund_company_financial_model_not_applicable`, which is correct but incomplete for a professional investment system.
- The existing portfolio risk budget work already has useful fund-adjacent evidence: SSGA SPY holdings import, benchmark composition coverage, active share, drift/outlier review, and position sizing review.
- This task reused existing `ref.benchmark_composition` holdings. No schema migration was required.
- EC2 evidence at commit `ea9a0dc`:
  - `/api/stocks/SPY` and `/api/recommendations/recommendation-157` return `fund_instrument_analysis.status=available`.
  - `benchmark_source=ssga_spdr_spy_daily_holdings`, `holding_count=503`, `holdings_coverage_weight=0.9983782`.
  - top holdings are `NVDA/AAPL/MSFT/AMZN/GOOGL`.
  - `/api/stocks/ARM` returns `fund_instrument_analysis=null` and keeps financial model `available`.
  - `/stocks/SPY` and `/recommendations/recommendation-157` route smoke confirmed the ETF/fund panel and read-only boundary text.

## Exact Next Step

- exact next step: start `fund-expense-tracking-source-v1` to add free/explicit-source handling for ETF expense ratio, tracking error/NAV drift, and liquidity evidence. Keep unknown states where source data is absent.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not synthesize company financials for ETF/fund-like instruments.
- Use free/public or already collected data only.
