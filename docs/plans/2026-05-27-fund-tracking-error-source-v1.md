# fund-tracking-error-source-v1 Plan

## Summary

SPY fund analysis now has source-backed holdings, liquidity, expense ratio, NAV, and market-price/NAV premium-discount evidence. The remaining ETF/fund metric gap is true multi-period tracking error or tracking difference. This task must not confuse one-day NAV premium/discount with tracking error.

## Implementation Order

1. Inspect official State Street SPDR product data and other free/public ETF sources for tracking error, tracking difference, and fund-vs-benchmark return windows.
2. Decide whether existing `market.fund_metric_snapshot` can store the metric with benchmark/window metadata or whether a narrowly scoped schema extension is needed.
3. Implement import only for source-backed values.
4. Expose the result on stock and recommendation detail in Korean.
5. If no acceptable free/public source exists, keep tracking error explicit unknown and record the blocker.

## Guardrails

- No paid provider.
- No guessed tracking error.
- No recommendation weight changes.
- No live broker submit.

## Result

- Implemented in commit `05cdd2a`.
- The official State Street SPDR product page does not publish a true tracking error metric, so true tracking error remains explicit unknown.
- The same page publishes month-end fund NAV return and S&P 500 Index benchmark return windows. The implementation imports those windows as `tracking_difference`, not `tracking_error`.
- EC2 import `run_id=1592` inserted eight SPY tracking difference metrics. The one-year value is `-0.0021`, with fund NAV return `0.3084`, benchmark return `0.3105`, benchmark `S&P 500 Index`, source date `2026-04-30`, and basis `nav_total_return_before_tax`.
- `/api/stocks/SPY`, `/api/recommendations/recommendation-157`, `/stocks/SPY`, and `/recommendations/recommendation-157` expose the result while preserving `order_boundary=read_only_no_order`.
