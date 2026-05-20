# Task Review

## Summary

- Recommendation detail score components now carry additive provenance.
- Market feature components are linked to the feature snapshot rows that feed recommendation scoring.
- `rank_score` is now represented as strategy universe rank provenance, not a price feature.
- The recommendation page renders the lineage in Korean: feature type, source run, observation window, and rank.
- No scoring formula, schema, benchmark, LLM/provider calls, broker/order, or scheduler behavior was changed.

## Verification Evidence

- API/unit: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v` passed.
- Frontend typecheck: `cd apps/web && npm run typecheck` passed.
- Frontend build: `cd apps/web && npm run build` passed.
- Live API smoke: `/api/recommendations/AAPL-2024-11-01` returned `quality_status=ready_for_human_review`, `pass_count=6`, `market_or_rank_component_count=3`, and `market_or_rank_provenance_count=3`.
- Browser check: `/recommendations/AAPL-2024-11-01` rendered “가격 지표”, `pipeline-run-8`, “전략 유니버스 2/3위”, and “근거 ID” as separate readable text. Screenshot: `/private/tmp/stockanalysis-runtime/market-feature-provenance-linking.png`.

## Residual Risks

- This is read-only explanatory lineage. It does not create a formal audit proof tying every stored component to an immutable input hash.
- Market feature lineage is inline on the recommendation page; there is still no standalone feature snapshot detail page.
- If future live runs produce missing `source_run_id` on feature rows, the market/rank provenance gate will warn rather than pass.
