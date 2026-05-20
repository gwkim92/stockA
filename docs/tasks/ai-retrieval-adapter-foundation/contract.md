# Task Contract

## Task

- 이름: ai-retrieval-adapter-foundation
- 요청: 무료/로컬 우선 원칙을 지키면서 AI RAG/ontology 도입의 최소 백엔드 경계를 만든다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태:
  - production vector DB, graph DB, external LLM 호출 없이 내부 retrieval adapter contract가 존재한다.
  - Postgres canonical tables 기반 evidence neighborhood SQL 렌더러가 존재한다.
  - ontology-lite graph consistency 검증 SQL 렌더러가 존재한다.
  - 다음 단계가 RAG/ontology runtime을 붙일 수 있도록 테스트와 검증 스크립트가 있다.

## Why

- 사용자는 AI RAG/ontology를 고려하되 무료여야 하고 토큰/비용을 줄여야 한다고 명시했다.
- 지금 프로젝트에는 `ai.document_chunk`, `ai.embedding_index`, `ref.classification_*`, `event.event_*_impact` 등 기반 테이블이 이미 있다.
- 따라서 pgvector, OpenAI vector store, Neo4j, GraphRAG를 바로 도입하기보다 내부 adapter와 Postgres graph query boundary를 먼저 고정한다.

## Scope

- 포함:
  - retrieval query/result dataclass와 deterministic in-memory adapter
  - Postgres evidence neighborhood SQL renderer
  - ontology-lite validation SQL renderer
  - targeted unit tests
  - verification script
  - task handoff/review 문서
- 제외:
  - DB migration
  - vector embedding 생성 또는 backfill
  - live LLM 호출
  - external vector DB, graph DB, RDF/SHACL runtime
  - recommendation scoring, benchmark, evaluation split 변경
  - frontend route/API DTO 변경
  - trading/broker/order flow 변경

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/ai/__init__.py`
  - `src/stockanalysis/ai/retrieval.py`
  - `src/stockanalysis/ai/evidence_graph.py`
  - `src/stockanalysis/ai/ontology_validation.py`
  - `tests/test_ai_retrieval.py`
  - `tests/test_ai_evidence_graph.py`
  - `tests/test_ai_ontology_validation.py`
  - `scripts/verify_ai_retrieval_adapter_foundation.sh`
  - `docs/verification-plan.md`
  - `docs/tasks/ai-retrieval-adapter-foundation/*`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ai_retrieval tests.test_ai_evidence_graph tests.test_ai_ontology_validation -v`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_retrieval_adapter_foundation.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-retrieval-adapter-foundation`
  - `git diff --check`

## Done Criteria

- [x] retrieval adapter boundary exists and is covered by unit tests.
- [x] evidence neighborhood SQL uses existing Postgres tables only.
- [x] ontology validation SQL renders read-only consistency checks.
- [x] verification script passes.
- [x] handoff and review record exact verification evidence.

## Verification Evidence

- command: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ai_retrieval tests.test_ai_evidence_graph tests.test_ai_ontology_validation -v`
- command: `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_retrieval_adapter_foundation.sh`
- command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task ai-retrieval-adapter-foundation`
- command: `git diff --check`

- First targeted test run failed as expected because `stockanalysis.ai.retrieval`, `stockanalysis.ai.evidence_graph`, and `stockanalysis.ai.ontology_validation` did not exist.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_ai_retrieval tests.test_ai_evidence_graph tests.test_ai_ontology_validation -v`
  - result: 9 tests passed.
- `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python bash scripts/verify_ai_retrieval_adapter_foundation.sh`
  - result: 9 tests passed and verification script printed `ai retrieval adapter foundation verification passed`.
