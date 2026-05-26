# recommendation-professional-decision-waterfall-v1 Handoff

## Current Status

- 완료: 추천 상세 API/화면에 전문 의사결정 waterfall를 추가했고 local/EC2 검증과 route smoke가 통과했다.

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
- Roadmap/harness:
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-professional-decision-waterfall-v1`
  - `git diff --check`
  - Result: passed
- EC2 deploy:
  - `/opt/stockanalysis/app` fast-forwarded to commit `96bc6db`.
  - Focused recommendation detail test: `Ran 1 test ... OK`
  - Adapter suite before final localization commit: `Ran 59 tests ... OK`
  - `apps/web` `npm run typecheck` and `npm run build`: passed
  - `stockanalysis-frontend-api.service` and `stockanalysis-web.service`: active
- EC2 API smoke:
  - `/api/recommendations/recommendation-147`
  - `professional_decision_waterfall.status=paper_validation_required`
  - step count `8`
  - step keys: `macro_cycle`, `news_ai`, `business_competition`, `financial_quality`, `valuation`, `thesis`, `position_sizing`, `paper_validation`
  - `news_direction=관찰`, `paper_outcome=성과 측정 전`
  - `order_boundary=read_only_no_order`, `automatic_order_allowed=false`, `broker_submit_allowed=false`
- EC2 route smoke through `http://127.0.0.1:13000`:
  - `/recommendations/recommendation-147`: `200`
  - contains `전문 의사결정 흐름`, `거시·사이클 배경`, `뉴스·AI 근거`, `사업·경쟁 위치`, `재무 품질`, `밸류에이션`, `투자 논리`, `포지션 크기`, `페이퍼 검증`, `추천 가중치 변경 없음`, `읽기 전용·주문 금지`
  - no remaining `broker submit`, `automatic order`, or `active weight` in the rendered route HTML

## Remaining Work

- The next professional-analysis gap is thesis lifecycle enforcement, not recommendation detail waterfall rendering.

## Exact Next Step

- exact next step: open `thesis-lifecycle-professional-gates-v1` and make each thesis expose catalyst, invalidation, risk, valuation context, review cadence, and stale evidence gates without changing recommendation weights or enabling broker orders.
