# Task Contract

## Task

- 이름: internal-rag-retrieval-foundation-v1
- 요청: 외부 유료 RAG/vector/graph 서비스 없이 Postgres canonical DB 기반 내부 RAG 검색 컨텍스트를 만든다.
- 담당: Codex
- 날짜: 2026-05-27

## Goal

- goal: `/api/ai/evidence-neighborhoods/{symbol}`가 기존 evidence graph와 함께 AI 배치 입력으로 바로 쓸 수 있는 `internal_rag_context`를 반환한다.
- `internal_rag_context`는 원천 뉴스/공시, 한국어 번역, 테마/그래프, AI artifact, 투자 논리, 추천, 보유 맥락을 read-only context package로 정규화한다.
- 새 CLI `stockanalysis-operations internal-rag-context-run`으로 EC2에서 특정 종목의 내부 RAG context를 repo-outside artifact로 점검할 수 있다.
- 외부 vector DB, Neo4j/RDF store, paid RAG service, FastAPI 요청 중 live LLM call, 추천 점수 변경, broker/order flow는 도입하지 않는다.

## Scope

- 포함:
  - `stockanalysis.ai.internal_rag` context package builder 추가
  - evidence neighborhood API DTO에 `internal_rag_context` 추가
  - TypeScript DTO와 종목 상세 화면에 내부 RAG 준비 상태 노출
  - read-only CLI preview 추가
  - unit/API/CLI/frontend 검증
  - task handoff/review 문서
- 제외:
  - DB migration
  - pgvector extension enablement
  - external vector DB 또는 graph DB
  - live LLM/provider call
  - recommendation scoring weight 변경
  - write API, broker submit, order flow

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ai/internal_rag.py`
  - `src/stockanalysis/frontend/live_adapter.py`
  - `src/stockanalysis/operations/cli.py`
  - `apps/web/src/lib/types.ts`
  - `apps/web/src/app/stocks/[symbol]/page.tsx`
  - `tests/test_internal_rag.py`
  - `tests/test_frontend_live_adapter.py`
  - `tests/test_data_operations_cli.py`
  - `scripts/verify_internal_rag_retrieval_foundation_v1.sh`
  - `docs/verification-plan.md`
  - `docs/tasks/internal-rag-retrieval-foundation-v1/*`

## Verification Commands

- verification command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_internal_rag tests.test_frontend_live_adapter tests.test_data_operations_cli`
- verification command: `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_internal_rag_retrieval_foundation_v1.sh`
- verification command: `cd apps/web && npm run typecheck`
- verification command: `cd apps/web && npm run build`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task internal-rag-retrieval-foundation-v1`
- verification command: `git diff --check`

## Done Criteria

- [ ] API response exposes `internal_rag_context` without secrets or vector storage URI.
- [ ] CLI preview runs read-only and can write repo-outside artifact.
- [ ] UI shows internal RAG readiness in user-facing Korean wording.
- [ ] Targeted backend/frontend verification passes.
- [ ] EC2 smoke proves the deployed service returns the new context.
- [ ] handoff/review record exact verification evidence and remaining risks.
