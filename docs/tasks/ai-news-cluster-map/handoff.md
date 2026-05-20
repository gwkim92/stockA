# Session Handoff

## Active Task

- 이름: ai-news-cluster-map
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract and plan created.
- `/api/ai/news-clusters` read-only live adapter endpoint implemented.
- Endpoint reads stored `news_cluster_summary` artifacts, model invocation metadata, source documents, document chunks, and embedding metadata.
- Endpoint redacts vector URI/secrets and exposes only counts/status/provider/model metadata.
- `/intelligence` now renders stored AI news cluster analysis with cluster count, event count, source document count, chunk/embedding readiness, cost boundary, AI evidence links, stock links, and source document links.
- `scripts/verify_ai_news_cluster_map.sh` added and referenced from `docs/verification-plan.md`.
- 진행 중:
  - none for this task.
- 막힌 점:
  - none currently.

## Exact Next Step

- 다음 세션은 이것부터 시작: decide whether to improve free semantic retrieval/ranking over RSS chunks, or add a dedicated source/news data room page for filtering clusters by theme/symbol/source.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_news_cluster_list_response_matches_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_news_cluster_list_sql_is_read_only -v`: 2 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_news_cluster_map.sh`: passed.
- `cd apps/web && npm run typecheck`: first run failed because `.next/types/routes.js` was missing before build; rerun after `npm run build` passed.
- `cd apps/web && npm run build`: passed.
- Live FastAPI `/api/ai/news-clusters?asOfDate=2026-05-19&limit=4`: cluster count 4, clustered event count 40, chunks 40, embedded chunks 40, local rule clusters 4, cost 0, no vector URI.
- Browser `http://127.0.0.1:3001/intelligence`: stored AI analysis section, AI news cluster count 4, embedding count 40, cost/no-live-LLM boundary, and AI evidence links are visible.

## Risks

- This task surfaces stored local-rule AI evidence. It does not add live LLM reasoning or semantic retrieval quality.
- RSS source chunk content currently comes from title/summary/URL, not full article body.
- This does not change recommendation scoring, benchmark, evaluation split, or trading flows.
