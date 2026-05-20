# Task Contract

## Task

- 이름: ai-retrieval-neighborhood-api
- 요청: AI evidence graph foundation을 read-only FastAPI/frontend 경계와 종목 상세 화면에 연결한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - `/api/ai/evidence-neighborhoods/{symbol}` read-only DTO가 존재한다.
  - endpoint는 기존 FastAPI read-token/auth/error/write-method boundary를 그대로 사용한다.
  - 종목 상세 화면에서 수집 이벤트, AI 증거, 청크/임베딩 상태, 투자 논리/추천/보유 연결을 하나의 관계망으로 볼 수 있다.
  - external vector DB, GraphDB, live LLM call, 추천 점수, 거래 flow는 변경하지 않는다.

## Scope

- 포함:
  - `stockanalysis.ai.evidence_graph` SQL renderer를 frontend live adapter에 연결
  - TypeScript DTO와 `frontend-api.ts` reader 추가
  - `/stocks/[symbol]` 화면에 AI 증거 관계망 섹션 추가
  - targeted backend/frontend tests and verification script
  - task handoff/review 문서
- 제외:
  - DB migration
  - embedding/vector backfill
  - live LLM/provider call
  - OpenAI vector store, pgvector, Neo4j, RDF/SHACL runtime
  - recommendation scoring, benchmark, evaluation split 변경
  - broker/order/write API 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/frontend/live_adapter.py`
  - `apps/web/src/lib/frontend-api.ts`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `apps/web/src/lib/korean-labels.ts`
  - `tests/test_frontend_live_adapter.py`
  - `scripts/verify_ai_retrieval_neighborhood_api.sh`
  - `docs/verification-plan.md`
  - `docs/tasks/ai-retrieval-neighborhood-api/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_ai_evidence_graph -v`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_retrieval_neighborhood_api.sh`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-retrieval-neighborhood-api`
  - `git diff --check`

## Done Criteria

- [x] read-only evidence neighborhood API DTO exists.
- [x] API does not expose vector storage URI or secrets.
- [x] stock detail page renders AI evidence neighborhood section.
- [x] targeted backend and frontend verification passes.
- [x] handoff/review record exact verification evidence.

## Verification Evidence

- command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_ai_evidence_graph -v`
- command: `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_retrieval_neighborhood_api.sh`
- command: `cd apps/web && npm run typecheck`
- command: `cd apps/web && npm run build`
- command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-retrieval-neighborhood-api`
- command: `git diff --check`

- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_ai_evidence_graph -v`
  - result: 38 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_retrieval_neighborhood_api.sh`
  - result: 5 targeted tests passed and verification script printed `ai retrieval neighborhood API verification passed`.
- `cd apps/web && npm run typecheck`
  - result: passed.
- `cd apps/web && npm run build`
  - result: passed.
- live FastAPI smoke for `/api/ai/evidence-neighborhoods/NVDA?asOfDate=2026-05-19&maxItems=12`
  - result: `postgres_sql`, `live_llm_call_enabled=false`, `ai_artifact_count=1`, `vector_uri_exposed=false`.
- browser check for `http://127.0.0.1:3001/stocks/NVDA`
  - result: visible page contains `AI 증거 관계망`, event/evidence counts, token boundary, AI evidence link, and no live LLM boundary copy.
