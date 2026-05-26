# Session Handoff

## Current Status

- 진행 중: persisted portfolio risk budget guardrail을 trading readiness DTO와 주요 화면에 연결했다. focused backend test와 typecheck/compileall은 일부 통과했고, full build/EC2 smoke가 남아 있다.

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

## Exact Next Step

- exact next step: EC2에 배포한 뒤 `/paper-trading`, `/trading-readiness`, `/portfolio/coverage` route smoke를 확인한다.
