# portfolio-gate-resolution-v1 Contract

## Purpose

포트폴리오 관련 `/data-health` open gate를 실제 장애와 관리 중인 투자 판단/성과 관찰 상태로 분리한다.

## Scope

- `benchmark_drift_quality_attention`
- `portfolio_review_decision_history_attention`
- `portfolio_review_decision_feedback_attention`
- `portfolio_review_feedback_calibration_attention`

## Rules

- 검토 결정, 성과 feedback, calibration runner가 최신 cadence로 연결되어 있고 주문·weight 변경이 차단되어 있으면 운영 장애 open gate로 보지 않는다.
- 모순 성과(`has_contradictions`), 원천 누락, unsafe order/weight guardrail은 계속 open gate로 둔다.
- 추천 weight, benchmark 정의, portfolio position, broker submit은 변경하지 않는다.

## Acceptance Criteria

- 최신 cadence가 `calibration_current`이고 action router가 직전 `feedback_executed` 상태여도, guardrail이 안전하면 history/benchmark gate가 관리 상태로 닫힌다.
- `needs_more_data` feedback은 `managed_current_feedback_collection`일 때 open gate에서 제외된다.
- `weight_review_blocked=true`와 `read_only_no_order`는 유지된다.
- 회귀 테스트가 stale router/current cadence 케이스를 고정한다.

## Verification

```bash
PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter
PYTHONPATH=src python3 -m compileall -q src tests
```
