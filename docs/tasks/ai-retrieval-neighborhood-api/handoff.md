# Session Handoff

## Active Task

- 이름: ai-retrieval-neighborhood-api
- 담당: Codex
- 날짜: 2026-05-19

## Current Status

- 완료:
  - task contract created.
- `/api/ai/evidence-neighborhoods/{symbol}` read-only live adapter path added.
- API DTO redacts `vector_storage_uri` and exposes only embedding status/provider/model metadata.
- `apps/web` stock detail reader and `AiEvidenceNeighborhoodData` type added.
- `/stocks/[symbol]` now renders `AI 증거 관계망` with event, AI evidence, chunk/embedding, thesis/recommendation, and guardrail context.
- verification script `scripts/verify_ai_retrieval_neighborhood_api.sh` added and referenced in `docs/verification-plan.md`.
- 진행 중:
  - none for this task.
- 막힌 점:
  - none.

## Exact Next Step

- 다음 세션은 이것부터 시작: decide whether to promote the evidence neighborhood to a dedicated `/ai/evidence-neighborhoods/{symbol}` detail page, or first add embedding chunk generation/backfill for RSS source documents.

## Verification

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_ai_evidence_graph -v`: 38 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_retrieval_neighborhood_api.sh`: passed.
- `cd apps/web && npm run typecheck`: passed.
- `cd apps/web && npm run build`: passed.
- Live FastAPI `/api/ai/evidence-neighborhoods/NVDA?asOfDate=2026-05-19&maxItems=12`: returned `postgres_sql`, `live_llm_call_enabled=false`, `ai_artifact_count=1`, and did not expose `vector_storage_uri`.
- Browser `http://127.0.0.1:3001/stocks/NVDA`: visible `AI 증거 관계망`, token boundary, AI evidence link, and no-live-LLM guardrail copy.

## Risks

- This task exposes existing relationships. It does not create production RAG quality, vector search, live LLM analysis, or recommendation automation.
- Current NVDA live data has event and AI artifact links but no document chunks/embedding rows yet, so the RAG-ready chunk area correctly shows an empty state.
