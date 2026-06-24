# broker-readiness-zero-weight-copy-reset-v1 Handoff

## Status

- completed: `broker_execution_readiness_score`, `broker_liquidity_warning`, `broker_price_basis_risk` zero-weight recommendation components were added.
- completed: component values are sourced from Toss read-only comparison, microdata, and stock warning snapshots when available.
- completed: recommendation detail API provenance now labels broker components as `broker_reality_context`.
- completed: recommendation detail UI now shows a dedicated `토스증권 실행 현실` section and keeps these components excluded from final score/rank impact.
- completed: high-impact visible copy was revised across home, recommendations, recommendation detail, paper trading, stocks, cycle map, cycles, intelligence, AI evidence, events classification, source documents, portfolio coverage, thesis detail, trading readiness, admin AI agents, and data-health.
- completed: copy pass removed direct user-facing uses of `사람 검토`, `AI가 한 일`, `canonical`, `shadow`, and most non-operator `fallback/pipeline/artifact/runner` wording from investment pages.
- completed: EC2 `/opt/stockanalysis/app` was fast-forwarded to commit `86d042d7` on `develop`.
- completed: EC2 recommendation bootstrap reran for `2026-06-23`, `long_term_core`, `long_term`, `live-20260623`, producing run `7316`, batch `38`, and active recommendation `recommendation-455`.
- completed: recommendation `recommendation-455` keeps ARM at rank `1` and score `0.733` while exposing the new broker components with weight `0.0`.

## Verification

- passed: `PYTHONPATH=src python3 -m py_compile src/stockanalysis/signal/recommendation.py src/stockanalysis/frontend/live_adapter.py`
- passed: `PYTHONPATH=src python3 -m unittest tests.test_recommendation_bootstrap tests.test_frontend_live_adapter`
- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `git diff --check`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task broker-readiness-zero-weight-copy-reset-v1`
- passed on EC2: `cd /opt/stockanalysis/app/apps/web && npm run typecheck && npm run build`
- passed on EC2: `systemctl is-active stockanalysis-frontend-api.service stockanalysis-web.service`
- passed on EC2/API: `/api/recommendations/recommendation-455` has broker components `broker_execution_readiness_score=0.8`, `broker_liquidity_warning=1.0`, `broker_price_basis_risk=0.75`, all `weight=0.0`, `source_type=broker_reality_context`.
- passed route smoke through `http://127.0.0.1:13000`: `/`, `/market-map`, `/cycle-map`, `/stocks/AAPL`, `/recommendations`, `/recommendations/recommendation-455`, `/paper-trading`, `/ai-evidence`, `/ai-evidence/results`, `/ai-evidence/blocked`, `/data-health`, `/portfolio/coverage`, `/admin/ai-agents` returned `200`.
- passed browser-rendered copy scan: `/`, `/market-map`, `/cycle-map`, `/stocks/AAPL`, `/recommendations/recommendation-455`, `/paper-trading`, `/ai-evidence/results`, `/data-health`, `/admin/ai-agents` had zero rendered hits for `canonical`, `shadow`, `pipeline`, `artifact`, `runner`, `fallback`, `LLM`, `human review`, `사람 검토`, `검토 가능`, `실패`.

## Invariants

- recommendation total score/rank/bucket/recommended weight were not intentionally changed.
- new Toss broker components use `component_weight=0.0000`.
- broker submit, automatic order, and live trading remain blocked.
- data-health remains the operator screen and may still expose execution-record terminology where it is useful for debugging.

## Next Step

- exact next step: review the actual visual hierarchy page-by-page with screenshots, starting with `/data-health`, `/recommendations/recommendation-455`, and `/stocks/AAPL`; copy is cleaned, but layout density and prioritization still need a separate visual pass.
