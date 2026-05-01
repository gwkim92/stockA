# Task Plan

## 1. Source Baseline

- 공식 OpenAI 문서에서 2026-04-23 기준 모델, Responses API, Prompt Caching, Retrieval, Structured Outputs, Function Calling, Batch API, Evals, Embeddings를 확인한다.
- Microsoft GraphRAG와 GraphRAG paper에서 plain RAG 한계와 graph-based summarization의 역할을 확인한다.
- W3C RDF/OWL/SHACL에서 ontology와 validation의 표준 방향을 확인한다.

## 2. Architecture Document

- `docs/ai-intelligence-architecture.md`를 만든다.
- AI가 맡는 영역과 맡지 않는 영역을 분리한다.
- RAG와 ontology/knowledge graph 병행 결정을 쓴다.
- token/cost governance와 quality gate를 쓴다.
- 다음 구현 단계를 `event-intelligence-llm-extract`로 고정한다.

## 3. AI Metadata Schema

- `db/migrations/0005_ai_intelligence.sql`을 만든다.
- `ai.prompt_template`, `ai.model_invocation`, `ai.document_chunk`, `ai.embedding_index`, `ai.extraction_artifact`, `ai.eval_run`을 추가한다.
- full raw text는 Postgres에 넣지 않고 hash, preview, metadata, pointer만 저장한다.

## 4. Verification

- `scripts/verify_ai_intelligence_architecture.sh`를 만든다.
- compileall과 전체 unittest를 실행한다.
- Docker Postgres에 migration/seed를 적용한다.
- AI schema tables 존재와 샘플 metadata insert를 검증한다.

## 5. Project Docs

- `README.md`에 새 문서와 검증 스크립트를 연결한다.
- `docs/verification-plan.md`에 새 검증 명령을 추가한다.
- `docs/db-schema-design.md`에 `ai` schema와 data management boundary를 추가한다.
- `docs/ai-role-map.md`에 architecture 문서와 다음 구현 위치를 연결한다.

## 6. Handoff

- 검증 결과를 `handoff.md`와 `review.md`에 남긴다.
- 남은 위험과 다음 구현 단계를 기록한다.
