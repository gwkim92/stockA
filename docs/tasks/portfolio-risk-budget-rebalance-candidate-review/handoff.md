# Session Handoff

## Current Status

- 완료: full SPY benchmark drift에서 리밸런싱 검토 후보를 만드는 backend DTO/UI 작업을 구현했고, EC2 API/route smoke까지 통과했다.

## Implementation Notes

- authoritative source는 `ai.eval_run`의 latest `portfolio_risk_budget_guardrail.score_json.benchmark_drift.top_active_positions`이다.
- 이번 작업은 주문 목표나 수량을 계산하지 않는다.
- 후보는 active weight의 절대값과 방향만 사용해 검토 우선순위를 만든다.
- overweight는 `trim_active_overweight_review`, underweight는 `review_active_underweight_gap`으로 노출한다.
- 모든 후보는 `order_boundary=read_only_no_order`를 유지한다.
- 후보 threshold는 active weight 절대값 `3%p` 이상이다.
- severity는 `high >= 20%p`, `medium >= 10%p`, 나머지는 `watch`이다.
- `/api/trading/readiness`와 `/api/portfolio/{portfolio}/coverage`는 같은 `rebalance_candidate_review` DTO를 노출한다.
- `/portfolio/coverage`, `/paper-trading`, `/trading-readiness`는 이 후보를 주문 후보가 아니라 검토 후보로만 표시한다.

## Verification

- Local focused:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
  - Result: `Ran 58 tests ... OK`
- Local full:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
  - Result: `Ran 939 tests ... OK`
- Local compile/type/build:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - Result: passed
- EC2 deploy:
  - `/opt/stockanalysis/app` fast-forwarded to commit `322667f`
  - `tests.test_frontend_live_adapter`: `Ran 58 tests ... OK`
  - `npm run typecheck` and `npm run build`: passed
  - `stockanalysis-frontend-api.service` and `stockanalysis-web.service`: active
- EC2 API smoke:
  - `/api/trading/readiness` `rebalance_candidate_review.status=review_required`
  - `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-26` `rebalance_candidate_review.status=review_required`
  - candidate count `7`
  - active share `0.77853213`
  - source `ssga_spdr_spy_daily_holdings`
  - top candidates: `TSLA`, `MSFT`, `AAPL`, `NVDA`, `AMZN`
  - `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`
- EC2 route smoke through `http://127.0.0.1:13000`:
  - `/portfolio/coverage`: `200`, contains `벤치마크 대비 리밸런싱 검토`, `TSLA`
  - `/paper-trading`: `200`, contains `리밸런싱 검토 후보`, `TSLA`
  - `/trading-readiness`: `200`, contains `리밸런싱 검토 후보`, `TSLA`

## Guardrails

- 추천 weight 변경 금지.
- broker submit/live order 금지.
- benchmark/evaluation split 변경 금지.
- repo 안 secret/env 값 수정 금지.

## Exact Next Step

- exact next step: `portfolio-position-sizing-policy-v1` task를 열고, 리밸런싱 검토 후보를 실제 주문 수량이 아니라 thesis quality, valuation margin, active risk, liquidity/cash buffer를 반영한 position sizing review envelope로 연결한다.
