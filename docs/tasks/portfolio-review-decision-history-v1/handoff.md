# portfolio-review-decision-history-v1 Handoff

## Status

- in progress: portfolio review decisions now have a backend CLI runner, `ai.eval_run` persistence, live API visibility, and frontend visibility. EC2 deployment/smoke evidence should be appended after push.
- blockers: none known.

## Context

- `benchmark-drift-outlier-decision-v1` exposes benchmark drift outliers as explicit read-only decisions in the current DTOs.
- Those decisions are still read-time derivations from the latest risk budget guardrail payload.
- Professional operation needs historical traceability: when a drift decision appeared, what source evidence drove it, whether it persisted, and whether later paper/outcome evidence validated it.
- This task uses `ai.eval_run` as the smallest durable storage boundary. A dedicated portfolio review table is deferred until history volume/query requirements justify it.
- New CLI: `stockanalysis-operations portfolio-review-decision-history-run --portfolio-name "Long Term Paper" --as-of-date YYYY-MM-DD --execute`.
- `/api/data-health` now exposes `portfolio_review_decision_history`.
- `/api/portfolio/{portfolio}/coverage` now exposes `risk_budget.review_decision_history`.

## Exact Next Step

- exact next step: deploy to EC2, execute `portfolio-review-decision-history-run`, and smoke `/api/data-health`, `/data-health`, `/api/portfolio/Long%20Term%20Paper/coverage`, and `/portfolio/coverage`.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
