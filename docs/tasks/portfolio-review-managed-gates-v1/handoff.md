# portfolio-review-managed-gates-v1 Handoff

## Status

- completed: managed review gate policy is implemented and local verification passed; EC2 deploy/smoke remains.

## Context

- Current EC2 open gates after source-gap refinement are `production_api_server`, `auth_rbac`, `alert_destination`, `data_operations_artifact_runner`, `benchmark_drift_quality_attention`, `portfolio_review_decision_history_attention`, and `portfolio_review_feedback_calibration_attention`.
- The benchmark/review gates are not data collection failures. They are portfolio concentration review states.
- The system already has decision history `eval-run-31` and action router `eval-run-35`, with `action_status=no_op_wait_for_outcome_window`.
- Implementation adds `attention_required`, `managed_review_status`, and `managed_review_reason` to benchmark drift quality and portfolio review decision history payloads.
- Benchmark drift remains an attention gate for source/guardrail problems such as partial composition, stale composition, or missing guardrail.
- Benchmark drift becomes managed when full-quality drift has outlier review decisions, review history is managed, and the action router is safely waiting for outcome observation.
- Portfolio review history becomes managed when decisions are persisted, all order/rebalance paths are read-only, and the action router is safely waiting for outcome observation.

## Exact Next Step

- exact next step: deploy to EC2 and confirm current benchmark/review-history gates close while the evidence remains visible.
