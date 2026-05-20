# Session Handoff

## Active Task

- 이름: recommendation-score-evidence-linking
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract created.
  - implementation plan created.
  - `render_frontend_recommendation_detail_state_sql()` now builds `recommendation_event_anchor` and `recommendation_evidence_anchor` CTEs.
  - Recommendation evidence anchor prefers `ai-evidence-{artifact_id}` and falls back to `event-{event_id}`.
  - Cycle/event-like score components now use the concrete evidence anchor when available.
  - Recommendation links expose a valid event ledger URL instead of unsupported event-detail URLs.
  - Recommendation page links `ai-evidence-*` to AI evidence detail and `event-*`/`sec-event-*` to event ledger.
  - FastAPI backend was restarted with the runtime venv and is serving the updated DTO on `127.0.0.1:8787`.
- 진행 중:
  - none.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: improve market-feature evidence lineage by linking `market-feature-*` components to the exact price window/provider run that produced them, or move to recommendation/thesis generation quality if price feature lineage is acceptable.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter -v` passed.
- `cd apps/web && npm run typecheck` passed.
- `cd apps/web && npm run build` passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task recommendation-score-evidence-linking` passed.
- `git diff --check` passed.
- Live API smoke: `/api/recommendations/AAPL-2024-11-01` returned `quality_status=ready_for_human_review`, `ai_evidence_component_count=1`, `pass_count=5`, `warning_count=0`, and `cycle_score.evidence_id=ai-evidence-1`.
- Browser evidence: `/private/tmp/stockanalysis-runtime/recommendation-score-evidence-linking.png`.

## Risks

- The anchor is a read-only explanatory evidence link, not proof that the score formula causally used that exact event.
- Market-feature components can still use feature ids because they come from price/market data, not document evidence.
- This does not change recommendation generation or trading behavior.
- The next lineage gap is market-feature provenance: momentum/rank/short-term score components still point to feature IDs rather than the exact price provider/run/window.
