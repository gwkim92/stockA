# recommendation-financial-model-waterfall-integration-v1 Handoff

## Status

- completed: implementation, local verification, GitHub push, EC2 deployment, and EC2 API/route smoke are complete.

## Current Status

The prior `financial-statement-model-detail-v1` slice is deployed and exposes stock-level `financial_statement_model`. This task now connects that same model semantics to recommendation detail.

## Current Findings

- Recommendation detail now exposes `financial_statement_model`.
- The professional decision waterfall `financial_quality` step now uses the financial model when present.
- The recommendation detail page now has a Korean financial model panel showing computed metrics, data gaps, share-count change, and key sections.

## Decisions

- This is a read-only visibility/integration slice.
- No scoring weights, benchmark splits, or order boundaries will be changed.
- Recommendation detail should reuse the same financial model semantics as stock detail.

## Exact Next Step

- exact next step: Start `valuation-model-quality-depth-v1` to deepen DCF-lite, relative multiple, scenario/sensitivity assumptions, and method evidence without changing recommendation weights.

## Verification Log

- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_recommendation_detail_response_matches_frontend_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_recommendation_detail_sql_links_score_components_to_event_or_ai_evidence`
- Passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src python3 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task recommendation-financial-model-waterfall-integration-v1`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed with Python 3.13 verify venv: `PYTHONPATH=src /private/tmp/stockanalysis-verify-venv/bin/python -m unittest discover -s tests` ran 940 tests OK.
- Note: default `python3` currently points to Homebrew Python 3.14 and fails unrelated XML/fastapi checks because of the known `pyexpat`/dependency environment issue. Python 3.13 verify venv is the authoritative local full-test evidence for this task.
- Pushed: `e58cfdb Expose financial model on recommendation detail`.
- EC2 deploy: `/opt/stockanalysis/app` fast-forwarded to `e58cfdb`.
- EC2 passed: focused recommendation detail tests, compileall, `npm run typecheck`, and `npm run build`.
- EC2 services restarted and active: `stockanalysis-frontend-api.service`, `stockanalysis-web.service`.
- EC2 API smoke: `/api/recommendations/recommendation-151` returned `symbol=NVDA`, `financial_statement_model.status=available`, `metric_count=14`, `computed_metric_count=12`, `data_gap_count=2`, `latest_period_end=2026-02-20`, `financial_quality.status=재무 모델 연결`, `score_policy=recommendation_weights_unchanged`, `order_boundary=read_only_no_order`, `automatic_order_allowed=false`, and `broker_submit_allowed=false`.
- EC2 route smoke: `/recommendations/recommendation-151` rendered `추천 재무제표 모델`, `계산 완료`, `이익 품질`, and `재무 모델 연결`.

## Remaining Risks

- The financial model depends on existing SEC/companyfacts and normalization coverage.
- The first version will show latest computed values and data gaps, not analyst forecasts or footnote-level adjustments.
- Some recommendation symbols can still show `financial_statement_model.status=unavailable` when normalized financial coverage is missing. The UI now surfaces that as a data gap rather than fabricating evidence.
