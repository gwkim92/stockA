# portfolio-position-sizing-policy-v1 Handoff

## Current Status

- 완료: backend DTO, unit test, frontend type, `/portfolio/coverage` UI first slice를 구현했고 EC2 API/route smoke까지 통과했다.

## Intent

The project needs professional portfolio risk management, not only news and cycle interpretation. This task adds the first read-only position sizing envelope so the cockpit can explain whether a holding is too large, too small, missing evidence, or acceptable for hold review.

## Current Guardrails

- Do not change recommendation score weights.
- Do not write order intents.
- Do not enable broker submit.
- Do not create hard target weights from benchmark drift.

## Implementation Notes

- The first slice should compose existing data instead of adding schema.
- Missing valuation or professional analysis should appear as evidence gaps.
- The UI should use Korean investment language and avoid operator-only wording.
- `risk_budget.position_sizing_review`는 read-only envelope이며 target weight나 order quantity가 아니다.
- 후보 구분은 `reduce_review`, `add_blocked_until_evidence`, `watch_small_position`, `hold_review` 네 가지다.
- `review_ceiling_weight`는 주문 목표가 아니라 검토 상한 참고값이다.
- 모든 후보는 `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`를 유지해야 한다.

## Verification

- Focused backend:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_portfolio_coverage_response_matches_frontend_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_portfolio_position_sizing_context_sql_is_read_only_professional_context`
  - Result: `Ran 2 tests ... OK`
- Adapter suite:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest tests.test_frontend_live_adapter`
  - Result: `Ran 59 tests ... OK`
- Compile/type/build:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src/stockanalysis/frontend/live_adapter.py tests/test_frontend_live_adapter.py`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - Result: passed
- Local full:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - Result: `Ran 940 tests ... OK`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `bash scripts/verify_project_execution_roadmap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-position-sizing-policy-v1`
  - Result: passed
- EC2 deploy:
  - `/opt/stockanalysis/app` fast-forwarded to commit `599eb71`.
  - `tests.test_frontend_live_adapter`: `Ran 59 tests ... OK`
  - `apps/web` `npm run typecheck` and `npm run build`: passed
  - `stockanalysis-frontend-api.service` and `stockanalysis-web.service`: active
- EC2 API smoke:
  - `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-26`
  - `position_sizing_review.status=review_required`
  - candidate count `4`
  - review required count `3`
  - reduce review count `3`
  - top candidates: `TSLA`, `MSFT`, `AAPL` as `reduce_review`; `NVDA` as `hold_review`
  - `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`
- EC2 route smoke through `http://127.0.0.1:13000`:
  - `/portfolio/coverage`: `200`
  - contains `포지션 크기 검토`, `증거 보강 전 증액 금지`, `벤치마크 대비 괴리`, `주문 전송`
  - no remaining `active weight`, `active risk`, or `broker submit` in the rendered route HTML

## Remaining Work

- Recommendation detail still needs a single professional decision waterfall that connects macro/cycle/news, company fundamentals, valuation, position sizing, thesis, and paper validation in one report-like page.

## Exact Next Step

- exact next step: `recommendation-professional-decision-waterfall-v1` task를 열고 추천 상세에서 거시→테마→기업→재무→밸류에이션→포지션 크기→thesis→가상 검증 흐름을 한 화면에서 추적 가능하게 만든다.
