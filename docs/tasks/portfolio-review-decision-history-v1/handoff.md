# portfolio-review-decision-history-v1 Handoff

## Status

- completed: portfolio review decisions now have a backend CLI runner, `ai.eval_run` persistence, live API visibility, frontend visibility, and EC2 execute/smoke evidence.
- EC2 deploy/smoke: completed on commit `e985dad`.
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

- exact next step: start `portfolio-review-decision-outcome-feedback-v1` by joining saved review decisions to later paper validation, recommendation outcome, thesis, and price evidence.

## EC2 Evidence

- EC2 commit: `e985dad`.
- Services: `stockanalysis-frontend-api.service` and `stockanalysis-web.service` active after restart.
- Runner: `stockanalysis-operations portfolio-review-decision-history-run --portfolio-name "Long Term Paper" --as-of-date 2026-05-25 --execute` completed with `run_id=1634`, `eval_run_id=31`.
- Runner output: `decision_status=review_required`, `decision_count=11`, `benchmark_decision_count=7`, `position_sizing_decision_count=4`, top decision `TSLA` / `비중 축소 검토`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`.
- `/api/data-health`: `portfolio_review_decision_history.status=loaded`, `eval_run_id=eval-run-31`, `decision_count=11`, `benchmark_decision_count=7`, `position_sizing_decision_count=4`, top decision `TSLA`.
- `/api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2026-05-25`: `risk_budget.review_decision_history.status=loaded`, `eval_run_id=eval-run-31`, `decision_count=11`, `review_required_count=10`, top decision `TSLA`, `broker_submit_allowed=false`.
- Route smoke through local tunnel returned `200` for `/`, `/data-health`, and `/portfolio/coverage`.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
