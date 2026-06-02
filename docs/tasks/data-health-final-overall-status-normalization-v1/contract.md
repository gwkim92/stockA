# data-health-final-overall-status-normalization-v1 Contract

## Task Request

- request: Fix `/api/data-health` showing `overall_status=attention_required` after all actionable `open_gates` have been closed.
- context: EC2 had `active_recommendation_price_freshness_attention` and `professional_source_gap_attention`; after price backfill and ADSK professional coverage expansion, `open_gates=[]` but `overall_status` still reflected the pre-policy SQL state.

## Goal

- goal: Derive the final data-health overall status from the final post-policy `open_gates`, not from stale raw SQL status.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `tests/test_frontend_live_adapter.py`
  - `docs/tasks/data-health-final-overall-status-normalization-v1/*`

## Invariants

- Do not hide managed source limits, outcome waits, or paper validation waits from their own cards.
- Do not remove any real actionable gate.
- Do not change recommendation score weights.
- Do not change benchmark definitions, portfolio positions, recommendations, theses, or paper outcomes.
- Do not enable broker submit, automatic orders, or automatic rebalancing.

## Scope

- Add a deterministic helper for data-health `overall_status`.
- If final `open_gates` is non-empty, status is `attention_required`.
- If final `open_gates` is empty and fallback is known, status is `healthy`.
- Preserve `unknown` only when the state is truly unknown and no final gates exist.

## Verification

- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
- verification command: `cd apps/web && npm run typecheck`
- verification command: EC2 `/api/data-health` smoke after deploy
- verification command: `http://127.0.0.1:13000/` and `/data-health` route smoke
