# data-health-attention-classification-v1 Handoff

## Status

- completed: local implementation, EC2 deploy, and route/API smoke passed.

## Context

- `portfolio-attribution-monthly-profile-integration-v1` removed the false missing monthly attribution gate.
- EC2 still reports `overall_status=attention_required`, but several remaining gates are expected investment review or outcome-wait states, not broken data collection.
- The current UI shows gate chips without explaining whether the user should fix infrastructure, review a portfolio concentration, wait for outcome maturity, or accept a known source limitation.
- Implementation keeps existing `open_gates` unchanged and adds structured details with `category`, `category_label`, `severity`, `status_label`, `summary`, `next_action`, `order_boundary`, and `automatic_action_allowed`.
- Current categories are `operational_blocker`, `investment_review`, `outcome_wait`, and `source_limit`.
- This is visibility-only. It does not close gates, change overall status, change recommendation weights, or enable broker/order actions.
- EC2 API smoke on commit `6dbeeec` returned `open_gate_count=8`, `open_gate_detail_count=8`, including `benchmark_drift_quality_attention` as `investment_review`, `portfolio_review_feedback_calibration_attention` as `outcome_wait`, and `professional_source_gap_attention` as `source_limit`.
- EC2 route smoke confirmed `/data-health` renders `벤치마크 괴리 검토`, `전문 분석 원천 한계`, `성과 관찰 대기`, `포트폴리오 검토 결정`, and `성숙한 검토 표본 0/10개`.

## Exact Next Step

- exact next step: use the classified gates to decide whether the next task should reduce a real data blocker, improve benchmark drift decision quality, or harden production operations.
