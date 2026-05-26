# Session Handoff

## Current Status

- 완료: persisted portfolio risk budget guardrail을 trading readiness DTO와 주요 화면에 연결했고, EC2에서 FastAPI/Next route smoke까지 확인했다.

## Implementation Notes

- `/api/trading/readiness`
  - `ai.eval_run`에서 최신 `portfolio_risk_budget_guardrail` eval을 읽는다.
  - `portfolio_risk_budget_guardrail` payload를 반환한다.
  - trading gate에 `포트폴리오 위험 예산`을 추가한다.
- `/paper-trading`
  - 위험 예산 카드와 최신 eval 기준일/벤치마크 drift 안내를 추가했다.
- `/trading-readiness`
  - 위험 예산 검증 상태와 blocker별 설명 카드를 추가했다.
- `/portfolio/coverage`
  - trading readiness DTO를 함께 읽어 persisted guardrail 상태를 보여준다.
- `koBlockedReason`
  - `portfolio_risk_budget_guardrail:*`
  - `portfolio_risk_budget_guardrail_blocker:*`
  - `over_single_position_limit`, `sector_over_limit`, `theme_over_limit` 등을 한국어로 매핑한다.

## Guardrails

- 추천 weight 변경 없음.
- paper validation writer 변경 없음.
- broker submit 없음.
- kill switch unlock 없음.

## Verification

- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- Passed: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- Passed: `cd apps/web && npm run typecheck`
- Passed: `cd apps/web && npm run build`
- Passed: `git diff --check`
- Passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-risk-budget-frontend-guardrail-visibility`
- Passed: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m unittest discover -s tests`
- Passed on EC2: pulled `b494474`, `stockanalysis-frontend-api.service` active, `stockanalysis-web.service` active.
- Passed on EC2: `cd apps/web && npm run build`
- Passed on EC2: `/paper-trading` contains `포트폴리오 위험 예산` and `입력 차단`.
- Passed on EC2: `/trading-readiness` contains `포트폴리오 위험 예산` and `위험 예산`.
- Passed on EC2: `/portfolio/coverage` contains `저장된 위험 예산 검증` and `벤치마크 drift`.
- Passed on EC2: `/api/trading/readiness` contains `portfolio_risk_budget_guardrail`.

## Exact Next Step

- exact next step: `portfolio-risk-budget-benchmark-composition-v1`을 진행한다. 현재 drift는 벤치마크 구성비가 없어 `insufficient_benchmark_composition`으로 명시적으로 미계산된다. 무료 benchmark composition source 또는 수동 seed를 추가해야 포트폴리오 drift를 계산할 수 있다.
