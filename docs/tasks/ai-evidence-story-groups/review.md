# Task Review

## Summary

- Added deterministic story groups to the AI evidence neighborhood DTO.
- Updated stock detail UI so users can see “뉴스 이야기 묶음”, why each group exists, how many events/source documents/RAG chunks are attached, and which representative event/source document to inspect.
- Kept the implementation read-only: no DB schema change, no paid LLM call, no vector DB, no recommendation scoring, no broker/order flow, and no scheduler activation.

## Verification Evidence

- Unit/API contract: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_ai_evidence_graph -v` passed.
- Frontend typecheck: `cd apps/web && npm run typecheck` passed.
- Frontend production build: `cd apps/web && npm run build` passed.
- Harness: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-evidence-story-groups` passed.
- Whitespace/syntax safety: `git diff --check` passed.
- Live API smoke: `/api/ai/evidence-neighborhoods/NVDA?asOfDate=2026-05-20&maxItems=12` returned `story_group_count=12`, first story basis `same_source_document`, `same_theme`, `same_title_signature`, and 3 linked chunks.
- Browser check: `/stocks/NVDA` renders “뉴스 묶음 12” and the “뉴스 이야기 묶음” panel. Screenshot: `/private/tmp/stockanalysis-runtime/stocks-nvda-story-groups-v2.png`.

## Residual Risks

- Grouping is deterministic and free, but still heuristic. It does not perform vector similarity, entity resolution, or LLM reasoning.
- Single-event groups can still appear because the panel also explains source/chunk attachment, not only multi-event duplicates.
- Some story groups can be ordered by freshest event rather than true investment importance; recommendation/thesis quality evaluation remains a separate task.
