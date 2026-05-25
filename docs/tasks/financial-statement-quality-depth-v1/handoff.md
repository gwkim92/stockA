# Session Handoff

## Current Status

- 완료:
  - task contract를 만들었다.
  - `financial_metric_normalization`에 `free_cash_flow_to_net_income`, `accrual_ratio`, `capex_intensity`, `liabilities_to_assets`를 추가했다.
  - `recommendation_fundamental_components`가 새 earnings quality/accruals와 liabilities/assets 지표를 zero-weight 입력으로 읽도록 연결했다.
  - focused unit test, compileall, diff check, AWH task verify를 통과했다.
  - EC2 실제 DB smoke로 새 지표 생성과 추천 component zero-weight 유지 여부를 확인했다.
  - EC2 FastAPI/Next.js 서비스를 재시작하고 health/home route를 확인했다.
- 진행 중:
  - 없음.
- 막힌 점:
  - 없음.

## Decisions

- 기존 `market.financial_metric_normalized`는 metric_code 확장을 허용하므로 DB schema migration은 필요 없다.
- 새 지표는 SEC companyfacts에서 이미 적재 중인 net income, operating cash flow, capex, revenue, total assets, liabilities를 조합한다.
- 추천 score/weight는 변경하지 않고 zero-weight fundamental component의 입력 품질만 높인다.
- `capex_intensity`는 산업별 해석 차이가 커서 첫 단계 추천 점수 입력에는 직접 사용하지 않고, normalization/peer universe에만 저장한다.

## Exact Next Step

- exact next step: `recommendation-quality-calibration` 또는 다음 professional equity layer task에서 outcome 표본 기반으로 새 fundamental 지표 설명력을 평가한다. 아직 추천 weight 변경은 금지다.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_professional_equity_analysis tests.test_recommendation_fundamental_components`
  - 결과: `Ran 17 tests ... OK`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - 결과: 통과
- `git diff --check`
  - 결과: 통과
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task financial-statement-quality-depth-v1`
  - 결과: `Task financial-statement-quality-depth-v1 passed readiness checks.`
- EC2 `PYTHONPATH=src /opt/stockanalysis/venv/bin/python -m unittest tests.test_professional_equity_analysis tests.test_recommendation_fundamental_components`
  - 결과: `Ran 17 tests ... OK`
- EC2 `financial-metric-normalization-run --as-of-date 2026-05-25 --execute`
  - 결과: `run_id=777`, 새 metric counts는 `accrual_ratio=872`, `capex_intensity=872`, `free_cash_flow_to_net_income=872`, `liabilities_to_assets=872`.
  - computed counts는 각각 `295`, `226`, `252`, `385`; 나머지는 원천 fact 부족으로 `unavailable` 유지.
- EC2 `recommendation-fundamental-components-run --as-of-date 2026-05-25 --execute`
  - 결과: `run_id=778`, component count `25`, `non_zero_weight_count=0`, `recommendation_total_score_mutated=false`.
- EC2 DB 확인
  - `signal.recommendation_score_component`의 fundamental/valuation/peer/balance-sheet/thesis component weight min/max는 모두 `0.0000`.
- EC2 service health
  - `stockanalysis-frontend-api.service`, `stockanalysis-web.service` 모두 `active (running)`.
  - `curl http://127.0.0.1:8787/__health` 성공, `curl -I http://127.0.0.1:3000/` 응답 `HTTP/1.1 200 OK`.
