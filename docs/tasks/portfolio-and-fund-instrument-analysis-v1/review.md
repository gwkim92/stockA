# portfolio-and-fund-instrument-analysis-v1 Review

## Review Summary

- Completed. SPY-like instruments now have a first-class `fund_instrument_analysis` payload and UI panel that uses benchmark holdings, portfolio role, and explicit unknown states for not-yet-collected expense/tracking data. Company financial models are no longer forced onto ETF/fund-like instruments.

## Issues Found

- The current slice still does not collect expense ratio, tracking error, NAV premium/discount, or liquidity evidence. These are visible as explicit `not_collected` states rather than guessed values.
- The portfolio coverage API path has a URL encoding boundary when called directly against FastAPI with `%20`; Next pages still use the intended frontend route. This was not changed in this task.

## Residual Risks

- Fund analysis currently depends on benchmark composition quality. SPY coverage is high (`0.9983782`), but other ETFs/funds may show source gaps until holdings are imported.
- No recommendation weights changed; fund analysis is visibility/evidence only.
- Live broker submit remains disabled.

## Verification Evidence

- Local verification before commit `f16e757` and fix commit `ea9a0dc`:
  - `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter` -> `Ran 61 tests OK`
  - `PYTHONPATH=src python3 -m compileall -q src tests` -> passed
  - `cd apps/web && npm run typecheck` -> passed
  - `cd apps/web && npm run build` -> passed
  - `git diff --check` -> passed
- EC2 deployment:
  - fast-forwarded to `ea9a0dc`
  - `/opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter` -> `Ran 61 tests OK`
  - `cd apps/web && npm run typecheck` -> passed
  - `stockanalysis-frontend-api.service` -> `active`
  - `stockanalysis-web.service` -> `active`
- EC2 API smoke:
  - `/api/stocks/SPY`: `fund_status=available`, `fund_source=ssga_spdr_spy_daily_holdings`, `fund_holding_count=503`, `fund_coverage=0.9983782`, top holdings `NVDA/AAPL/MSFT/AMZN/GOOGL`, `order_boundary=read_only_no_order`.
  - `/api/recommendations/recommendation-157`: same SPY fund analysis evidence.
  - `/api/stocks/ARM`: `fund_status=None`, `financial_status=available`, `source_blocker=None`, `order_boundary=read_only_no_order`.
- Route smoke through `http://127.0.0.1:13000`:
  - `/stocks/SPY` contains `ETF·펀드 분석`, holdings/exposure wording, or `ssga_spdr_spy_daily_holdings`.
  - `/recommendations/recommendation-157` contains `ETF·펀드 추천 검토`, holdings/portfolio role wording, or `ssga_spdr_spy_daily_holdings`.
  - recommendation detail contains read-only order boundary wording.
