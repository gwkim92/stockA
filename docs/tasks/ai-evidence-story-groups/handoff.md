# Session Handoff

## Active Task

- 이름: ai-evidence-story-groups
- 담당: Codex
- 날짜: 2026-05-20

## Current Status

- 완료:
  - task contract created.
  - implementation plan created.
  - `/api/ai/evidence-neighborhoods/{symbol}` now emits deterministic `story_groups`.
  - Story groups are built read-only at the live adapter boundary from existing events and evidence chunks.
  - Each story group includes representative title, events, source documents, linked chunk ids, grouping basis, relation reasons, latest event time, and heuristic confidence.
  - `apps/web/src/lib/types.ts` now includes `story_group_count` and `story_groups`.
  - `/stocks/{symbol}` now renders a Korean “뉴스 이야기 묶음” section inside the AI evidence panel.
  - FastAPI backend was restarted with the runtime venv and is serving the updated DTO on `127.0.0.1:8787`.
- 진행 중:
  - none.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: decide whether to improve story grouping with actual local semantic similarity, or move into recommendation/thesis quality evaluation using the now-visible evidence groups.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_ai_evidence_graph -v` passed.
- `cd apps/web && npm run typecheck` passed.
- `cd apps/web && npm run build` passed.
- `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-evidence-story-groups` passed.
- `git diff --check` passed.
- Live API smoke: `/api/ai/evidence-neighborhoods/NVDA?asOfDate=2026-05-20&maxItems=12` returned `story_group_count=12`; first story linked 3 RAG chunks.
- Browser evidence: `/private/tmp/stockanalysis-runtime/stocks-nvda-story-groups-v2.png`.

## Risks

- Title-token grouping is heuristic and can under-group or over-group related news.
- This improves explainability but is not semantic vector retrieval or live LLM reasoning.
- Existing canonical event/document rows are not modified.
- Current story confidence is a deterministic display heuristic, not an investment-quality score.
