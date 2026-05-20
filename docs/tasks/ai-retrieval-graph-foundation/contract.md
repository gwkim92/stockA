# Task Contract

## Task

- 이름: ai-retrieval-graph-foundation
- 요청: RAG, graph, ontology, Dagster류 orchestration 도입 여부와 후속 구현 범위를 다른 세션이 충돌 없이 이해하고 이어받을 수 있게 고정한다.
- 담당: Codex
- 날짜: 2026-05-03

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 다른 세션은 현재 프로젝트에 이미 있는 graph/RAG/ontology 기반, 아직 없는 runtime/tooling, 다음에 추가해야 할 최소 구현 단위, 수정 금지 영역을 task 문서만 읽고 이해할 수 있다.

## Why

- AI/RAG/GraphRAG/ontology/Dagster는 범위가 크고 서로 다른 파일 소유권을 건드리기 쉽다.
- 현재 저장소는 Postgres canonical state와 deterministic runner를 먼저 안정화하는 흐름이다.
- 대형 tool을 바로 도입하면 AGENTS/roadmap이 정의한 현재 immediate next task와 AI runtime 순서가 흔들릴 수 있다.
- 다음 세션이 같은 결정을 다시 조사하거나 기존 Postgres graph를 우회하지 않도록 repo-local handoff가 필요하다.

## Current Baseline

- 이미 있음:
  - `ops.pipeline_run` 기반 pipeline provenance
  - `ref.classification_node`, `ref.classification_edge` 기반 ontology-lite graph
  - `ref.instrument_classification_membership`
  - `event.event_classification_impact`, `event.event_instrument_impact`
  - `ai.prompt_template`, `ai.model_invocation`, `ai.document_chunk`, `ai.embedding_index`, `ai.extraction_artifact`, `ai.eval_run`
- 아직 없음:
  - Dagster, Airflow, Prefect 같은 orchestration framework
  - 실제 vector store runtime
  - pgvector extension migration
  - OpenAI vector store adapter
  - Neo4j/RDF triple store
  - GraphRAG indexing pipeline
  - SHACL/OWL validation runtime

## Scope

- 포함:
  - 현재 구현 상태와 guardrail 문서화
  - retrieval adapter boundary 정의
  - Postgres graph query boundary 정의
  - ontology-lite validation 후보 정의
  - future tool adoption 기준 정의
  - 다음 세션용 plan/handoff 작성
- 제외:
  - DB migration 추가
  - production vector DB 선택
  - live LLM provider call
  - embedding backfill 실행
  - GraphRAG indexing 구현
  - Dagster/Prefect/Airflow 도입
  - recommendation scoring 변경
  - benchmark/evaluation split 변경
  - frontend route/API DTO 변경
  - scheduler/deployment/secret 설정 변경
  - broker/order/trading automation

## Mutable Surface

- 수정 가능한 파일:
  - `docs/ai-intelligence-architecture.md`
  - `docs/project-execution-roadmap.md`
  - `docs/plans/2026-05-03-ai-retrieval-graph-foundation.md`
  - `docs/tasks/ai-retrieval-graph-foundation/`
- 수정 금지 파일:
  - `db/migrations/`
  - `src/stockanalysis/`
  - `apps/web/`
  - `tests/`
  - `scripts/`
  - env/secret/deployment files
  - files owned by the active frontend/API immediate task

## Ownership Boundaries For Future Implementation

- DB/schema owner:
  - owns `db/migrations/`, `docs/db-schema-design.md`
  - must not change benchmark, scoring, or evaluation split without explicit task contract
- Retrieval adapter owner:
  - should introduce an internal adapter before choosing pgvector/OpenAI vector stores/external vector DB
  - should read/write through `ai.document_chunk` and `ai.embedding_index` metadata
- Graph query owner:
  - should use existing `ref.classification_*`, `event.event_*_impact`, thesis, portfolio, and performance tables
  - should expose evidence neighborhoods before introducing a graph DB
- AI runtime owner:
  - should implement model gateway/eval/structured validation before prompt-only copilot features
- Frontend owner:
  - should not add new AI-facing routes until backend retrieval/evidence contracts exist
- Orchestration owner:
  - should keep current runner plus `ops.pipeline_run` pattern until retry/backfill/dependency complexity justifies a pilot

## Proposed Next Build Unit

- 이름 후보: `ai-retrieval-adapter-foundation`
- 최소 목표:
  - define retrieval query/input/output dataclasses
  - add deterministic graph neighborhood SQL for `event -> theme -> instrument -> thesis -> portfolio`
  - add adapter interface for vector search without choosing a production vector backend
  - add SQL validation checks for ontology-lite graph consistency
  - add unit tests and a Docker smoke only after schema/runtime scope is explicit

## Verification Commands

- 검증에 사용할 명령:
  - `rg -n 'Current Implementation Status|ai-retrieval-graph-foundation|Dagster|vector store|ontology-lite|Current task:|현재 고정된 immediate next task' docs/ai-intelligence-architecture.md docs/project-execution-roadmap.md docs/tasks/ai-retrieval-graph-foundation docs/plans/2026-05-03-ai-retrieval-graph-foundation.md AGENTS.md`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ai-retrieval-graph-foundation`

- 문서 검증:
  - `rg -n "Current Implementation Status|ai-retrieval-graph-foundation|Dagster|vector store|ontology-lite" docs/ai-intelligence-architecture.md docs/project-execution-roadmap.md docs/tasks/ai-retrieval-graph-foundation docs/plans/2026-05-03-ai-retrieval-graph-foundation.md`
  - `git diff --check`
- 하네스 검증 후보:
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ai-retrieval-graph-foundation`

## Deliverables

- 필수 결과물:
  - `docs/tasks/ai-retrieval-graph-foundation/contract.md`
  - `docs/tasks/ai-retrieval-graph-foundation/plan.md`
  - `docs/tasks/ai-retrieval-graph-foundation/handoff.md`
  - `docs/plans/2026-05-03-ai-retrieval-graph-foundation.md`
  - `docs/ai-intelligence-architecture.md` current implementation status update
  - `docs/project-execution-roadmap.md` future AI retrieval/graph task note

## Completion Criteria

- [x] 다른 세션이 현재 있음/없음/나중 후보를 문서에서 바로 확인할 수 있다.
- [x] AGENTS/roadmap이 정의한 current immediate next task를 바꾸지 않는다.
- [x] production vector DB, graph DB, orchestration framework를 도입하지 않는다.
- [x] 수정 가능한 파일 범위를 벗어나지 않는다.
- [x] 검증 명령 결과와 남은 위험을 handoff 또는 review에 남긴다.

## Rollback Or Fallback

- 문서 변경만 되돌리면 이전 상태로 돌아간다.
- 코드, schema, benchmark, scoring, deployment 변경이 없어야 한다.

## Open Questions

- 질문: 첫 vector backend는 pgvector, OpenAI vector stores, external vector DB 중 무엇인가?
- 임시 답: 선택하지 않는다. 먼저 internal retrieval adapter와 metadata contract를 만든다.

- 질문: graph traversal이 복잡해질 때 Neo4j/RDF/GraphRAG 중 무엇을 파일럿할 것인가?
- 임시 답: Postgres evidence neighborhood SQL로 병목을 확인한 뒤 작은 sector/theme corpus에서만 파일럿한다.

- 질문: Dagster류 orchestration은 언제 필요한가?
- 임시 답: current runner plus `ops.pipeline_run`이 retry/backfill/dependency visibility를 감당하지 못하는 증거가 생길 때 별도 task로 평가한다.
