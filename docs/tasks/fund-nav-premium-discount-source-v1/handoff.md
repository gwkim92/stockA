# fund-nav-premium-discount-source-v1 Handoff

## Status

- completed: source-backed SPY NAV and market-price/NAV premium-discount evidence is implemented, deployed, and EC2-smoked.

## Context

- `fund-expense-ratio-public-source-v1` completed on commit `b8f6e76`.
- `fund-nav-premium-discount-source-v1` completed on commit `5073119`.
- SPY fund analysis now has SSGA holdings, market price liquidity, official expense ratio, official NAV, official bid/ask midpoint, official closing price, and official premium/discount evidence.
- True multi-period tracking error remains explicitly unknown and must not be inferred from one-day premium/discount.

## Exact Next Step

- exact next step: start `fund-tracking-error-source-v1` to find a free/public, auditable multi-period benchmark-return source or keep true tracking error explicit unknown.

## Implementation Evidence

- Added migration `db/migrations/0028_fund_nav_premium_discount_metrics.sql`.
- Added CLI `stockanalysis-operations fund-nav-premium-discount-ssga-spdr-import-run`.
- Added source-backed metric codes in `market.fund_metric_snapshot`: `nav_per_share`, `bid_ask_midpoint`, `closing_price`, `premium_discount_to_nav`.
- Added API/frontend DTO field `fund_instrument_analysis.nav_premium_discount`.
- Added Korean stock/recommendation detail visibility with `NAV 괴리`, source link, NAV, closing price, and premium/discount.
- EC2 import: `run_id=1582`, `fund_metric_snapshot_ids=[2,3,4,5]`.
- EC2 source values: NAV `745.571145`, bid/ask midpoint `745.60`, closing price `745.64`, premium/discount `0.00`, source as-of date `2026-05-22`.
- EC2 API smoke: `/api/stocks/SPY` and `/api/recommendations/recommendation-157` return `nav_premium_discount.status=collected`, `premium_discount_to_nav=0.0`, source `ssga_spdr_product_page`, and `order_boundary=read_only_no_order`.
- EC2 route smoke: `/stocks/SPY` and `/recommendations/recommendation-157` render `NAV 괴리`, `NAV 원천 열기`, `US$745.57`, `0%`, `비용률`, and `주문 경계`.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not calculate premium/discount unless NAV and market price are both source-backed with disclosed dates.
- Do not label premium/discount as tracking error.
