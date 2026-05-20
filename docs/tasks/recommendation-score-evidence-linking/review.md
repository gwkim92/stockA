# Task Review

## Summary

- Linked recommendation score components to concrete event/AI evidence where source evidence exists.
- The recommendation detail SQL now finds a read-only evidence anchor for the recommendation instrument and date, preferring an AI artifact and falling back to an event id.
- The recommendation detail page now links concrete `ai-evidence-*` ids to AI evidence detail and event ids to the event ledger.
- No scoring formula, schema, benchmark, LLM, broker/order, or scheduler behavior was changed.

## Verification Evidence

- API/unit: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v` passed.
- Frontend typecheck: `cd apps/web && npm run typecheck` passed.
- Frontend build: `cd apps/web && npm run build` passed.
- Harness: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-score-evidence-linking` passed.
- Whitespace/syntax safety: `git diff --check` passed.
- Live API smoke: `/api/recommendations/AAPL-2024-11-01` returned `quality_status=ready_for_human_review`, `ai_evidence_component_count=1`, `pass_count=5`, `warning_count=0`, and the first score component `cycle_score` linked to `ai-evidence-1`.
- Browser check: `/recommendations/AAPL-2024-11-01` rendered “사람 검토 가능” and linked `ai-evidence-1` to `/ai-evidence/ai-evidence-1`. Screenshot: `/private/tmp/stockanalysis-runtime/recommendation-score-evidence-linking.png`.

## Residual Risks

- The evidence anchor is explanatory lineage, not a causal proof that the score formula used exactly that artifact.
- Market feature components still use `market-feature-*` ids. A follow-up should link those to price window/provider/run provenance.
- This does not make a recommendation investable by itself; it only removes the “missing concrete evidence id” quality warning.
