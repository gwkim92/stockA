# benchmark-drift-outlier-decision-v1 Handoff

## Status

- completed: benchmark drift outliers now produce explicit read-only portfolio review decisions in API payloads and frontend visibility.
- EC2 deploy/smoke: completed on commit `feefc84`.
- blockers: none known.

## Context

- `source-blocked-recommendation-guardrail-v1` completed on EC2 commit `da93536`.
- EROK recommendation `recommendation-67` is now blocked for professional decision use and paper validation input.
- `/api/data-health` still reports `benchmark_drift_quality_attention`.
- Latest known drift evidence from prior tasks: SSGA SPY composition coverage `0.9983782`, active share `0.77853213`, and top active positions such as `TSLA`, `MSFT`, and `AAPL`.

## Exact Next Step

- exact next step: start `portfolio-review-decision-history-v1` by choosing the durable storage boundary for these read-only review decisions.

## Implementation Notes

- `/api/data-health` `benchmark_drift_quality` now includes `outlier_decisions`, `review_candidate_count`, `review_decision_counts`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, and `order_boundary=read_only_no_order`.
- `/api/portfolio/{portfolio}/coverage` `risk_budget.rebalance_candidate_review.candidates` now includes `review_decision`, `decision_label`, `next_review_action`, source evidence, related thesis/recommendation fields when available, `decision_path`, and read-only order boundaries.
- The frontend data-health drift section now shows the review decision and next action for outlier symbols.
- The portfolio coverage rebalance table now shows the decision label, next action, linked recommendation/thesis context when available, and explicit broker-submit prohibition.
- Recommendation scoring weights, benchmark definition, portfolio positions, and broker/order behavior were not changed.

## EC2 Evidence

- EC2 commit: `feefc84`.
- Services: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active after restart.
- `/api/data-health` benchmark drift quality: `status=drift_outlier_review`, `review_candidate_count=7`, decision counts `reduce_watch=3`, `needs_thesis_update=3`, `hold_with_thesis=0`, `review_required=1`, `order_boundary=read_only_no_order`.
- `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25` rebalance review: `status=review_required`, `candidate_count=7`, decision counts `reduce_watch=3`, `needs_thesis_update=3`, `hold_with_thesis=1`, `review_required=0`, first candidate `TSLA` linked to `thesis-1` and `recommendation-61`, `broker_submit_allowed=false`.
- Route smoke through local tunnel returned `200` for `/`, `/data-health`, and `/portfolio/coverage`.

## Guardrails

- Keep recommendation scoring weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
- Treat this as professional review visibility and auditability, not execution.
