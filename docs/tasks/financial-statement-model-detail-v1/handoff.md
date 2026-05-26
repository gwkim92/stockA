# financial-statement-model-detail-v1 Handoff

## Status

- completed: implemented, verified locally, deployed to EC2, and live-smoked through the local tunnel.

## Current Status

Implementation is complete for the stock detail financial model visibility slice. `/api/stocks/{symbol}` exposes `financial_statement_model`, and `/stocks/[symbol]` renders the model in Korean without changing recommendation weights or order boundaries.

## Current Findings

- `market.financial_metric_normalized` already stores computed/unavailable/insufficient-history rows.
- `recommendation_fundamental_components` already consumes some normalized metrics as zero-weight evidence.
- Stock detail currently exposes equity research, industry competitive position, and valuation target range, but not the underlying financial statement model.

## Decisions

- This task is a read-only visibility slice.
- No new schema, no new financial formulas, and no recommendation weight changes.
- The model will be grouped by analyst sections rather than raw metric-code lists.
- For each metric, the DTO prefers the latest computed value when the latest filing period has an unavailable row. Latest-period data gaps remain visible in counts and per-metric status instead of making the whole model look empty.

## Exact Next Step

- exact next step: Start `recommendation-financial-model-waterfall-integration-v1` so recommendation detail uses the same full financial statement model behind the financial-quality step.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_stock_detail_response_matches_frontend_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_stock_sql_uses_canonical_tables`.
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`.
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`.
- Passed: `cd apps/web && npm run typecheck`.
- Passed: `cd apps/web && npm run build`.
- Passed: `bash scripts/verify_project_execution_roadmap.sh`.
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task financial-statement-model-detail-v1`.
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests` (`940 tests`).
- EC2 read-only SQL smoke using locally generated stock detail SQL passed for AAPL: `metric_count=14`, `computed_metric_count=12`, `unavailable_metric_count=2`, `latest_period_end=2025-10-17`, `share_count_latest=14776353000.0`.
- Committed and pushed as `9968a5c Expose financial statement model on stock detail`.
- EC2 `/opt/stockanalysis/app` fast-forwarded to `9968a5c`.
- EC2 focused live adapter tests passed for stock detail contract and SQL coverage.
- EC2 `cd apps/web && npm run typecheck` passed.
- EC2 `cd apps/web && npm run build` passed.
- EC2 `stockanalysis-frontend-api.service` and `stockanalysis-web.service` restarted and reported `active`.
- EC2 `/__health` returned `status=ok`.
- EC2 API smoke: `/api/stocks/AAPL` returned `financial_statement_model.status=available`, `metric_count=14`, `computed_metric_count=12`, `data_gap_count=2`, `section_count=7`, `first_section=growth`, `order_boundary=read_only_no_order`, and `automatic_order_allowed=false`.
- Local tunnel route smoke: `http://127.0.0.1:13000/stocks/AAPL` returned `200 OK` and rendered `재무제표 모델`, `계산 완료`, `이익 품질`, and `주식수 변화`.
- One parallel typecheck/build run failed because `.next/types/validator.ts` was missing during concurrent `.next` mutation; rerunning typecheck alone after build passed.

## Remaining Risks

- Financial model quality depends on existing SEC/companyfacts coverage and normalization quality.
- Missing or unavailable metrics must be visible so users do not mistake absent data for healthy fundamentals.
- This task does not yet embed the full financial model directly into recommendation detail; `recommendation-financial-model-waterfall-integration-v1` should connect this stock-level model into the recommendation waterfall.
