# portfolio-gate-resolution-v1 Handoff

## 2026-07-04

Root cause:

- EC2의 portfolio feedback runner/cadence는 최신까지 실행됐다.
- 그러나 `/data-health` 정책은 `portfolio_review_feedback_action_router.action_status`가 `feedback_executed`로 남아 있으면 최신 `portfolio_review_feedback_cadence.cadence_status=calibration_current`를 안전한 관리 상태로 인정하지 않았다.
- 그래서 실제 실행 누락이 아니라 관리 중인 성과 관찰/표본 보강 상태가 open gate로 남았다.

Changes:

- `src/stockanalysis/frontend/live_adapter.py`
  - 최신 cadence가 `calibration_current` 또는 `wait_for_outcome_window`이고 주문/weight guardrail이 안전하면 safe managed state로 인정한다.
  - history/benchmark drift gate는 최신 cadence가 안전하면 `current_feedback_cadence` 관리 상태로 닫힌다.
  - calibration은 `managed_current_feedback_collection` 상태를 추가해 충분한 feedback/mature sample과 zero contradiction 상태를 open gate가 아닌 관리 상태로 표현한다.
  - `needs_more_data` feedback은 위 관리 상태일 때 open gate에서 제외한다.

Evidence:

- passed: `PYTHONPATH=src python3 -m unittest tests.test_frontend_live_adapter`
- passed: `PYTHONPATH=src python3 -m compileall -q src tests`

Pending:

- Commit, push, EC2 `git pull --ff-only origin develop`, service restart.
- EC2 `/api/data-health` open gates 확인.

Boundaries:

- Recommendation weights unchanged.
- Benchmark definition unchanged.
- Portfolio positions unchanged.
- Broker submit remains disabled.
- `order_boundary=read_only_no_order` remains required.
