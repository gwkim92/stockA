# portfolio-review-managed-gates-v1 Handoff

## Status

- completed: managed review gate policy is implemented, verified locally, deployed to EC2, and route/API-smoked.

## Context

- Current EC2 open gates after source-gap refinement are `production_api_server`, `auth_rbac`, `alert_destination`, `data_operations_artifact_runner`, `benchmark_drift_quality_attention`, `portfolio_review_decision_history_attention`, and `portfolio_review_feedback_calibration_attention`.
- The benchmark/review gates are not data collection failures. They are portfolio concentration review states.
- The system already has decision history `eval-run-31` and action router `eval-run-35`, with `action_status=no_op_wait_for_outcome_window`.
- Implementation adds `attention_required`, `managed_review_status`, and `managed_review_reason` to benchmark drift quality and portfolio review decision history payloads.
- Benchmark drift remains an attention gate for source/guardrail problems such as partial composition, stale composition, or missing guardrail.
- Benchmark drift becomes managed when full-quality drift has outlier review decisions, review history is managed, and the action router is safely waiting for outcome observation.
- Portfolio review history becomes managed when decisions are persisted, all order/rebalance paths are read-only, and the action router is safely waiting for outcome observation.
- EC2 API smoke on commit `2694332` returned `benchmark_attention_required=false`, `benchmark_managed_review_status=review_recorded_waiting_for_outcome`, active share `0.77853213`, `history_attention_required=false`, `history_managed_review_status=waiting_for_outcome_window`, `history_decision_count=11`, and `history_review_required_count=10`.
- EC2 open gates dropped from 7 to 5 and no longer include `benchmark_drift_quality_attention` or `portfolio_review_decision_history_attention`.
- EC2 `/data-health` route smoke renders `큰 괴리 검토 관리 중`, `검토 이력 관리 중`, and `검토 결정은 저장됐고 자동 주문은 차단`, while raw `benchmark drift quality attention` and `portfolio review decision history attention` are absent.

## Exact Next Step

- exact next step: continue with the remaining open gates. The only investment-process gate left is `portfolio_review_feedback_calibration_attention`, which should stay open until enough mature feedback exists.
