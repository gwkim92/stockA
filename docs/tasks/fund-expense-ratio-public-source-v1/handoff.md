# fund-expense-ratio-public-source-v1 Handoff

## Status

- completed: official source-backed expense ratio import, DB storage, API/DTO exposure, frontend rendering, EC2 import smoke, and route smoke are complete.

## Context

- `fund-expense-tracking-source-v1` completed on commit `450d5e9`.
- SPY fund analysis has SSGA holdings source and `market.daily_price_bar` liquidity evidence.
- The SSGA holdings artifact still contains holdings only, so this task added a separate official product-page source path.
- New table: `market.fund_metric_snapshot`.
- New runner: `stockanalysis-operations fund-expense-ratio-ssga-spdr-import-run`.
- Official source: `https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy`.
- EC2 import evidence: `run_id=1581`, `fund_metric_snapshot_id=1`, `metric_code=gross_expense_ratio`, `metric_value=0.000945`, `percent_value=0.094500`, `source_as_of_date=2026-05-26`, `source_name=ssga_spdr_product_page`.
- API evidence: `/api/stocks/SPY` and `/api/recommendations/recommendation-157` return `expense_ratio.status=collected`, `expense_ratio.value=0.000945`, `expense_ratio.source_name=ssga_spdr_product_page`, `expense_ratio.source_as_of_date=2026-05-26`.
- ARM remains on company financial model path and does not receive fund analysis.

## Exact Next Step

- exact next step: start `fund-nav-premium-discount-source-v1` to collect source-backed NAV, market-price/NAV gap, and premium/discount evidence without guessing tracking error.

## Guardrails

- Keep recommendation weights unchanged.
- Keep broker/order flow read-only.
- Do not hard-code expense ratio constants.
- Do not implement tracking error/NAV in this slice.

## Verification Evidence

- Local: `PYTHONPATH=src python3 -m unittest tests.test_fund_expense_ratio_provider` passed, 5 tests.
- Local: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter` passed, 61 tests.
- Local: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli` passed, 77 tests.
- Local: `PYTHONPATH=src python3 -m compileall -q src tests` passed.
- Local: `cd apps/web && npm run typecheck` passed.
- Local: `cd apps/web && npm run build` passed.
- Local: `git diff --check` passed.
- Local source dry-run parsed official SSGA page as `metric_value=0.000945`, `percent_value=0.094500`, `source_as_of_date=2026-05-26`.
- EC2: fast-forwarded `/opt/stockanalysis/app` to commit `b8f6e76`.
- EC2: applied `db/migrations/0027_fund_metric_snapshot.sql`.
- EC2: focused Python tests passed, 143 tests.
- EC2: `cd apps/web && npm run typecheck` passed.
- EC2: `cd apps/web && npm run build` passed.
- EC2: official SSGA import executed with `run_id=1581`, `fund_metric_snapshot_id=1`.
- EC2: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` are active after restart.
- EC2 API: `/api/stocks/SPY` and `/api/recommendations/recommendation-157` expose collected expense ratio while preserving liquidity and read-only order boundary.
- Route smoke: `http://127.0.0.1:13000/stocks/SPY` and `/recommendations/recommendation-157` render `0.0945%`, `비용률 원천 열기`, `ssga_spdr_product_page`, `2026-05-26`, `유동성`, and `주문 경계`.
