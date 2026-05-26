# Session Handoff

## Current Status

- 완료: `/api/data-health`와 `/data-health`에 benchmark drift 품질 요약을 노출했고, EC2 smoke까지 확인했다.

## Implementation Notes

- data-health는 최신 `portfolio_risk_budget_guardrail` eval의 `benchmark_drift`를 읽어야 한다.
- 품질 판정은 사용자 판단 보조 정보이며 추천 점수나 주문 가능 여부를 바꾸지 않는다.
- partial benchmark composition은 full benchmark drift로 표현하면 안 된다.
- 새 payload: `benchmark_drift_quality`
  - `status`: `ok`, `partial_composition`, `stale_composition`, `missing_benchmark_composition`, `missing_guardrail`, `drift_outlier_review`
  - coverage/source/active share/outlier checks를 함께 반환한다.
- `/data-health`는 “벤치마크 drift 품질” 섹션에서 구성비 커버리지, 구성 기준일, active share, 큰 괴리 종목, 다음 조치를 한국어로 표시한다.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter tests.test_portfolio_risk_budget_guardrail`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests` with `934 tests OK`.
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `bash scripts/verify_project_execution_roadmap.sh`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-drift-quality-audit`
- Passed: `git diff --check`
- Passed on EC2: pulled `80e104b`.
- Passed on EC2: `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_portfolio_risk_budget_guardrail`
- Passed on EC2: `cd apps/web && npm run typecheck && npm run build`
- Passed on EC2: restarted `stockanalysis-frontend-api.service` and `stockanalysis-web.service`; both are active.
- Passed on EC2 API: `/api/data-health` returns `benchmark_drift_quality.status=partial_composition`, `composition_coverage_weight=0.215`, `active_share=0.3925`, `benchmark_source=operator_spy_holdings_2026_05_25`, `outliers=3`, and `benchmark_drift_quality_attention=true`.
- Passed route smoke: `http://127.0.0.1:13000/data-health` returns 200 and contains `벤치마크 drift 품질`, `부분 구성비로만 계산됨`, `구성비 커버리지`, `Active share`, and `큰 괴리 종목`.

## Known Limits

- 현재 EC2 benchmark source는 여전히 partial operator upload다. 이 작업은 partial 상태를 숨기지 않고 화면에 드러내는 것이며, full SPY holdings source 확보는 다음 task다.

## Guardrails

- 추천 weight 변경 금지.
- benchmark/evaluation split 변경 금지.
- broker submit, live order, kill switch unlock 금지.
- repo 안 secret/env 값 수정 금지.

## Exact Next Step

- exact next step: `portfolio-risk-budget-full-holdings-source`를 진행한다. partial operator smoke file을 full-enough free provider holdings file 또는 더 넓은 operator upload holdings set으로 대체한다.
