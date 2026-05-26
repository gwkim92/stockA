# recommendation-professional-decision-waterfall-v1 Handoff

## Current Status

- 완료: 로컬 추천 상세 API/화면에 전문 의사결정 waterfall를 추가했고 focused/full backend tests, compileall, Next typecheck/build가 통과했다.

## Intent

The project should behave like a professional long-term equity research and portfolio operating system. Recommendation detail must not look like a scattered list of scores. It should explain the full decision path from macro/cycle/news evidence to company fundamentals, valuation, thesis, position sizing, and paper validation.

## Current Guardrails

- Do not change recommendation score weights.
- Do not create order quantities or target weights.
- Do not enable broker submit or live orders.
- Keep the page and DTO read-only.
- Prefer existing canonical/read adapter data before adding schema.

## Implementation Notes

- Existing recommendation detail already has score components, equity research, industry competitive position, evidence trace, evidence review, and outcome.
- The new DTO should compose those fields into a stable `professional_decision_waterfall` rather than duplicating SQL-heavy business logic.
- The position sizing step should use current holding review context on recommendation detail and link to `/portfolio/coverage` for full portfolio-level sizing.
- The frontend should use the DTO waterfall first, not reconstruct a different order from scattered fields.
- Added `professional_decision_waterfall` with eight steps: `macro_cycle`, `news_ai`, `business_competition`, `financial_quality`, `valuation`, `thesis`, `position_sizing`, `paper_validation`.
- Every waterfall step preserves `automatic_order_allowed=false`, `broker_submit_allowed=false`, and `order_boundary=read_only_no_order`.
- The frontend maps backend waterfall steps into `ProfessionalResearchFlow`; existing detail sections remain drill-down evidence.

## Verification

- Focused backend:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_recommendation_detail_response_matches_frontend_contract_shape`
  - Result: `Ran 1 test ... OK`
- Adapter suite:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - Result: `Ran 59 tests ... OK`
- Full backend:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - Result: `Ran 940 tests ... OK`
- Compile/type/build:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - Result: passed

## Remaining Work

- Run roadmap verifier, AWH verify, and diff check after roadmap/handoff update.
- Commit, push, deploy to EC2, restart FastAPI/Next.js, and smoke API/route through `http://127.0.0.1:13000`.

## Exact Next Step

- exact next step: run AWH verification for `recommendation-professional-decision-waterfall-v1`, commit/push the verified changes, deploy to EC2, and route-smoke `/api/recommendations/{id}` plus `/recommendations/{id}`.
