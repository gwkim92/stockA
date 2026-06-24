# broker-readiness-zero-weight-copy-reset-v1 Handoff

## Status

- completed: `broker_execution_readiness_score`, `broker_liquidity_warning`, `broker_price_basis_risk` zero-weight recommendation components were added.
- completed: component values are sourced from Toss read-only comparison, microdata, and stock warning snapshots when available.
- completed: recommendation detail API provenance now labels broker components as `broker_reality_context`.
- completed: recommendation detail UI now shows a dedicated `토스증권 실행 현실` section and keeps these components excluded from final score/rank impact.
- completed: high-impact visible copy was revised across home, recommendations, recommendation detail, paper trading, stocks, cycle map, cycles, intelligence, AI evidence, events classification, source documents, portfolio coverage, thesis detail, trading readiness, admin AI agents, and data-health.
- completed: copy pass removed direct user-facing uses of `사람 검토`, `AI가 한 일`, `canonical`, `shadow`, and most non-operator `fallback/pipeline/artifact/runner` wording from investment pages.

## Verification

- passed: `PYTHONPATH=src python3 -m py_compile src/stockanalysis/signal/recommendation.py src/stockanalysis/frontend/live_adapter.py`
- passed: `PYTHONPATH=src python3 -m unittest tests.test_recommendation_bootstrap tests.test_frontend_live_adapter`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`

## Invariants

- recommendation total score/rank/bucket/recommended weight were not intentionally changed.
- new Toss broker components use `component_weight=0.0000`.
- broker submit, automatic order, and live trading remain blocked.
- data-health remains the operator screen and may still expose execution-record terminology where it is useful for debugging.

## Next Step

- exact next step: run AWH verify, commit the task on `develop`, push, deploy to EC2, rerun recommendation bootstrap/decision profile if needed so existing recommendations get the new zero-weight broker components, then smoke `/`, `/recommendations`, one `/recommendations/{id}`, `/stocks/AAPL`, `/paper-trading`, and `/data-health`.
