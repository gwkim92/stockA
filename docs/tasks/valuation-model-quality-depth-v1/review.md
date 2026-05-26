# valuation-model-quality-depth-v1 Review

## Review Status

- status: complete

## Implemented

- `valuation_target_range.methods[]` now includes method-level upside, valuation gap, Korean evidence summary, structured assumptions, sensitivity cases, data quality, and model limitations.
- `valuation_target_range.valuation_quality` now summarizes method coverage, confidence, warnings, data gaps, and the read-only order boundary.
- Future `market.valuation_snapshot.assumptions_json` output from the valuation runner now records model family, sensitivity basis, key variables, data quality, and Korean model limitations.
- The shared valuation card used by stock, recommendation, and thesis detail pages renders assumption quality, assumption items, bear/base/bull sensitivity, warnings, and limitations in Korean.
- Non-numeric assumption fields such as `price_date` are handled as text instead of crashing numeric formatting.

## Guardrails Checked

- Recommendation score weights were not changed.
- Benchmark split logic was not changed.
- Automatic order and broker submit remain disabled.
- No DB schema migration was added.

## Verification

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_stock_detail_response_matches_frontend_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_recommendation_detail_response_matches_frontend_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_thesis_detail_response_matches_frontend_contract_shape tests.test_professional_equity_analysis.ProfessionalEquityAnalysisTests.test_valuation_snapshot_upsert_sql_creates_three_methods_without_recommendation_mutation`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter tests.test_professional_equity_analysis`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m compileall -q src tests`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` (`Ran 940 tests in 5.166s`, `OK`)
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-verify-venv/bin/python -m awh verify --repo . --task valuation-model-quality-depth-v1`

## EC2 Evidence

- Deployed commit: `713ae61`.
- Remote build passed: `cd /opt/stockanalysis/app/apps/web && npm run build`.
- Restart passed: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` returned `active`.
- API smoke passed: `/api/stocks/NVDA`, `/api/recommendations/recommendation-151`, and `/api/theses/thesis-5` expose available valuation ranges with method count `3`, method-level assumptions, sensitivity cases, limitations, and `order_boundary=read_only_no_order`.
- Route smoke passed: `/stocks/NVDA`, `/recommendations/recommendation-151`, and `/theses/thesis-5` returned 200 and rendered `가정 품질` plus `모델 한계와 데이터 경고 보기`.
- Local tunnel smoke passed: `http://127.0.0.1:13000/` returned HTTP 200.

## Next

- `financial-forecast-and-scenario-inputs-v1`: build explicit forecast inputs behind DCF/scenario valuation before any recommendation weight change.
