# recommendation-financial-model-waterfall-integration-v1 Handoff

## Status

- local verified: implementation is complete locally; EC2 deploy and route/API smoke remain.

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

- exact next step: Deploy to EC2, restart FastAPI/Next services, then smoke `/api/recommendations/recommendation-147` and `/recommendations/recommendation-147`.

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

## Remaining Risks

- The financial model depends on existing SEC/companyfacts and normalization coverage.
- The first version will show latest computed values and data gaps, not analyst forecasts or footnote-level adjustments.
- EC2 runtime smoke is still pending until deployment.
