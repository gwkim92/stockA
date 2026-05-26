# data-health-attention-classification-v1 Handoff

## Status

- completed: local implementation and verification passed; EC2 deploy and smoke are the remaining operational follow-up.

## Context

- `portfolio-attribution-monthly-profile-integration-v1` removed the false missing monthly attribution gate.
- EC2 still reports `overall_status=attention_required`, but several remaining gates are expected investment review or outcome-wait states, not broken data collection.
- The current UI shows gate chips without explaining whether the user should fix infrastructure, review a portfolio concentration, wait for outcome maturity, or accept a known source limitation.
- Implementation keeps existing `open_gates` unchanged and adds structured details with `category`, `category_label`, `severity`, `status_label`, `summary`, `next_action`, `order_boundary`, and `automatic_action_allowed`.
- Current categories are `operational_blocker`, `investment_review`, `outcome_wait`, and `source_limit`.
- This is visibility-only. It does not close gates, change overall status, change recommendation weights, or enable broker/order actions.

## Exact Next Step

- exact next step: deploy to EC2, restart FastAPI/Next.js, and smoke `/api/data-health` plus `/data-health` for the new gate detail cards.
