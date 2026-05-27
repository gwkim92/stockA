# portfolio-feedback-calibration-maturity-visibility-v1

## Summary

- 남은 투자 프로세스 gate인 `portfolio_review_feedback_calibration_attention`을 숨기지 않는다.
- 대신 왜 추천 weight 변경이 금지인지, 어떤 성과 표본이 부족한지, 언제 outcome window가 성숙하는지를 API와 화면에서 명확히 보여준다.
- 이 작업은 recommendation scoring, benchmark, portfolio position, broker/order flow를 바꾸지 않는다.

## Scope

- `/api/data-health`의 `portfolio_review_feedback_calibration` payload에 성숙 상태, 예상 성숙일, 부족 feedback run 수, 부족 성숙 판단 수, weight 차단 이유를 추가한다.
- `/api/portfolio/{portfolio}/coverage`의 `risk_budget.review_feedback_calibration`도 같은 visibility를 사용한다.
- `/data-health`는 운영자용 코드가 아니라 사용자가 이해할 수 있는 문장으로 “성과 관찰 대기”와 “weight 변경 금지”를 보여준다.
- `wait_until`이 비어 있어도 `history.as_of_date + min_horizon_days`로 예상 성숙일을 계산한다.

## Non-Goals

- 추천 score weight를 변경하지 않는다.
- outcome row를 임의 생성하지 않는다.
- portfolio rebalance, paper order, broker submit을 실행하지 않는다.
- `portfolio_review_feedback_calibration_attention` gate를 성급히 닫지 않는다.

## Verification

- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- `cd apps/web && npm run typecheck`
- `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- `bash scripts/verify_project_execution_roadmap.sh`
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task portfolio-feedback-calibration-maturity-visibility-v1`
