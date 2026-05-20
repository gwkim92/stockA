# Task Contract

## Task

- 이름: ai-news-cluster-map
- 요청: 저장된 RSS 뉴스 AI 묶음 분석과 chunk/index 준비 상태를 API와 `/intelligence` 화면에 노출한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/ai/news-clusters` read-only DTO가 존재한다.
  - DTO는 `news_cluster_summary` artifact, 관련 이벤트, 원천 문서, chunk/embedding count, 비용/토큰 경계를 보여준다.
  - `/intelligence` 화면에서 “저장된 AI 뉴스 묶음”을 사람이 이해할 수 있는 문장과 링크로 볼 수 있다.
  - vector URI, DB URL, secrets, write/trading/order flow는 노출하거나 변경하지 않는다.

## Scope

- 포함:
  - live adapter read-only SQL renderer
  - frontend API type/client
  - `/intelligence` UI section
  - targeted tests and verification script
  - task handoff/review 문서
- 제외:
  - DB migration
  - paid news API
  - live LLM call
  - external vector DB/GraphDB
  - recommendation scoring, benchmark, evaluation split 변경
  - broker/order/write API 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/frontend/pagination.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/app/intelligence/page.tsx`
  - `tests/test_frontend_live_adapter.py`
  - `scripts/verify_ai_news_cluster_map.sh`
  - `docs/verification-plan.md`
  - `docs/plans/2026-05-19-ai-news-cluster-map.md`
  - `docs/tasks/ai-news-cluster-map/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_news_cluster_list_response_matches_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_news_cluster_list_sql_is_read_only -v`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_news_cluster_map.sh`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-news-cluster-map`
  - `git diff --check`

## Done Criteria

- [x] `/api/ai/news-clusters` exists and uses read-only SQL.
- [x] DTO redacts vector URI/secrets.
- [x] `/intelligence` renders stored AI cluster analysis and RAG readiness.
- [x] targeted backend/frontend verification passes.
- [x] handoff/review record exact evidence and residual risks.

## Verification Evidence

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_news_cluster_list_response_matches_contract_shape tests.test_frontend_live_adapter.FrontendLiveAdapterTests.test_live_ai_news_cluster_list_sql_is_read_only -v`
  - result: 2 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_news_cluster_map.sh`
  - result: passed and printed `AI news cluster map verification passed`.
- `cd apps/web && npm run typecheck`
  - first run failed because `.next/types/routes.js` was missing before build; after `next build` regenerated `.next/types`, rerun passed.
- `cd apps/web && npm run build`
  - result: passed.
- Live FastAPI smoke:
  - endpoint: `/api/ai/news-clusters?asOfDate=2026-05-19&limit=4`
  - result: cluster count 4, clustered event count 40, source document count 40, chunk count 40, embedded chunk count 40, local rule cluster count 4, estimated cost `$0.0000`, no `vector_storage_uri`.
- Browser smoke:
  - URL: `http://127.0.0.1:3001/intelligence`
  - result: visible stored AI analysis section, AI news cluster count 4, embedding count 40, no-live-LLM/cost boundary, AI evidence links.
