# portfolio-review-decision-history-v1 Handoff

## Status

- in progress: task contract created as the next professional portfolio-risk hardening step; implementation has not started.
- blockers: none known.

## Context

- `benchmark-drift-outlier-decision-v1` exposes benchmark drift outliers as explicit read-only decisions in the current DTOs.
- Those decisions are still read-time derivations from the latest risk budget guardrail payload.
- Professional operation needs historical traceability: when a drift decision appeared, what source evidence drove it, whether it persisted, and whether later paper/outcome evidence validated it.

## Exact Next Step

- exact next step: inspect existing `eval_run`, `ops.pipeline_run`, and portfolio/risk schemas to choose the smallest durable storage boundary for review decision history.

## Guardrails

- Keep recommendation score weights unchanged.
- Keep broker/order flow read-only.
- Do not mutate benchmark composition or portfolio positions.
