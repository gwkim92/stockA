# financial-statement-model-detail-v1 Handoff

## Status

- in progress: local implementation, full local verification, AWH verification, and read-only EC2 SQL smoke passed; commit/deploy verification pending.

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

- exact next step: Run final full verification, commit, push, deploy to EC2, then smoke `/api/stocks/AAPL` and `/stocks/AAPL`.

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
- One parallel typecheck/build run failed because `.next/types/validator.ts` was missing during concurrent `.next` mutation; rerunning typecheck alone after build passed.

## Remaining Risks

- Financial model quality depends on existing SEC/companyfacts coverage and normalization quality.
- Missing or unavailable metrics must be visible so users do not mistake absent data for healthy fundamentals.
- This task does not yet embed the full financial model directly into recommendation detail; current next logical slice is to connect this stock-level model into the recommendation waterfall.
