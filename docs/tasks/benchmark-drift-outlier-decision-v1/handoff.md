# benchmark-drift-outlier-decision-v1 Handoff

## Status

- in progress: task contract and plan are created; implementation has not begun.
- blockers: none known.

## Context

- `source-blocked-recommendation-guardrail-v1` completed on EC2 commit `da93536`.
- EROK recommendation `recommendation-67` is now blocked for professional decision use and paper validation input.
- `/api/data-health` still reports `benchmark_drift_quality_attention`.
- Latest known drift evidence from prior tasks: SSGA SPY composition coverage `0.9983782`, active share `0.77853213`, and top active positions such as `TSLA`, `MSFT`, and `AAPL`.

## Exact Next Step

- exact next step: inspect live EC2 `/api/data-health` and `/api/portfolio/Long%20Term%20Paper/coverage` benchmark drift/rebalance candidate payloads, then decide where deterministic outlier decisions should be attached.

## Guardrails

- Keep recommendation scoring weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
- Treat this as professional review visibility and auditability, not execution.
