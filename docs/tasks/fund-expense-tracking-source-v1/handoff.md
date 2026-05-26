# fund-expense-tracking-source-v1 Handoff

## Status

- completed: implemented, pushed, deployed to EC2, and smoked on commit `450d5e9`.

## Context

- `portfolio-and-fund-instrument-analysis-v1` completed on commit `ea9a0dc`.
- SPY fund analysis currently has high-quality holdings evidence from `ssga_spdr_spy_daily_holdings`.
- Existing SSGA holdings artifact was inspected and contains holdings fields only. It does not provide auditable expense ratio, NAV, premium/discount, or tracking error fields.
- Liquidity now uses the already collected `market.daily_price_bar` source. SPY has `liquidity.status=collected`, source `market.daily_price_bar`, `observation_count=100`, `average_daily_volume=75546352.24`, and `average_daily_dollar_volume=51757628999.20085` on EC2.
- Expense ratio and tracking error/NAV drift remain intentionally `not_collected`; they must not be guessed.

## Exact Next Step

- exact next step: `fund-expense-ratio-public-source-v1`; find a free auditable public expense-ratio source and add a source-backed import/DTO path, or keep explicit unknown if no source can be validated.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Use free/public or already collected data only.
- Preserve explicit unknown states when no auditable source exists.

## Verification Evidence

- Local: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter` passed, 61 tests.
- Local: `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- Local: `cd apps/web && npm run typecheck` passed.
- Local: `cd apps/web && npm run build` passed.
- Local: `git diff --check` passed.
- EC2: fast-forwarded `/opt/stockanalysis/app` to `450d5e9`.
- EC2: `/opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter` passed, 61 tests.
- EC2: `cd apps/web && npm run typecheck` passed.
- EC2: `cd apps/web && npm run build` passed.
- EC2: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` are active after restart.
- EC2 API: `/api/stocks/SPY` and `/api/recommendations/recommendation-157` return `fund_instrument_analysis.status=available`, `liquidity.status=collected`, source `market.daily_price_bar`, observation count `100`, expense ratio `not_collected`, tracking error `not_collected`, and `order_boundary=read_only_no_order`.
- EC2 API: `/api/stocks/ARM` remains a company financial model path with `financial_status=available` and no fund analysis.
- Route smoke: `http://127.0.0.1:13000/stocks/SPY` and `/recommendations/recommendation-157` render `유동성`, `평균 거래량`, `평균 거래대금`, and `주문 경계`.
