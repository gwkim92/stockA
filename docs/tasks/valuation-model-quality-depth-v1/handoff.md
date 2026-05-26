# valuation-model-quality-depth-v1 Handoff

## Status

- in progress: DTO, future assumptions JSON, shared valuation card, and tests are implemented; local verification passed; EC2 deployment and API/route smoke are still pending.

## Current Findings

- `market.valuation_snapshot` already stores method, base price, low/base/high fair values, margin of safety, assumptions JSON, confidence, and source run.
- `valuation_target_range` already appears on stock, recommendation, and thesis detail pages through a shared card.
- Current display is too shallow for professional analysis because it does not expose method assumptions, sensitivity, data quality, or model limitations.

## Decisions

- This is a read-only evidence-depth slice.
- No schema migration is required; richer future assumptions can live in existing `assumptions_json`.
- The frontend live adapter will derive useful evidence even from older snapshots that only have basic assumptions.
- Recommendation weights, benchmark splits, and order boundaries remain unchanged.
- Non-numeric assumption values such as `price_date` are formatted as plain text instead of being forced through numeric parsing.

## Exact Next Step

- exact next step: commit/push, deploy to EC2, then smoke `/api/stocks/{symbol}`, `/api/recommendations/{id}`, and matching routes for valuation quality fields.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_stock_detail_response_matches_frontend_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_recommendation_detail_response_matches_frontend_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_thesis_detail_response_matches_frontend_contract_shape tests.test_professional_equity_analysis.ProfessionalEquityAnalysisTests.test_valuation_snapshot_upsert_sql_creates_three_methods_without_recommendation_mutation`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_professional_equity_analysis`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m compileall -q src tests`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 940 tests in 5.166s`, `OK`)
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-verify-venv/bin/python -m awh verify --repo . --task valuation-model-quality-depth-v1`
- Pending: EC2 API/route smoke.

## Remaining Risks

- Existing EC2 valuation snapshots may have old shallow assumptions until `valuation-snapshot-run` is rerun.
- DCF-lite remains a simplified model; the UI must label it as evidence, not a precise target-price claim.
- This task does not yet create explicit revenue/margin/FCF forecast tables; that should be the next valuation depth task before any scoring weight change.
