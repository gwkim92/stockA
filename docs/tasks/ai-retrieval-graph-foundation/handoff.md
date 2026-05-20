# Session Handoff

## Active Task

- 이름: ai-retrieval-graph-foundation
- 담당: Codex
- 날짜: 2026-05-03

## Current Status

- 완료:
  - RAG/graph/ontology/orchestration의 현재 있음/없음 상태를 task contract로 고정했다.
  - 후속 구현 순서를 `plan.md`에 정리했다.
  - 다른 세션이 볼 standalone implementation plan 위치를 정했다.
  - AI architecture 문서에 current implementation status를 추가했다.
  - roadmap AI Runtime 구간에 retrieval/graph foundation guardrail을 추가했다.
  - 문서 검색, whitespace, task harness readiness 검증을 통과했다.
- 막힌 점:
  - 아직 없음.

## Files Touched

- 생성:
  - `docs/tasks/ai-retrieval-graph-foundation/contract.md`
  - `docs/tasks/ai-retrieval-graph-foundation/plan.md`
  - `docs/tasks/ai-retrieval-graph-foundation/handoff.md`
  - `docs/plans/2026-05-03-ai-retrieval-graph-foundation.md`
- 수정:
  - `docs/ai-intelligence-architecture.md`
  - `docs/project-execution-roadmap.md`
- 의도적으로 안 건드린 것:
  - active frontend/API immediate task files
  - `db/migrations/`
  - `src/stockanalysis/`
  - `tests/`
  - `scripts/`
  - secrets/deployment config

## Decisions

- 결정:
  - 현재 프로젝트에는 Postgres 기반 ontology-lite graph와 AI metadata schema가 있다.
  - 현재 프로젝트에는 Dagster류 orchestrator, real vector store runtime, graph DB, GraphRAG indexing runtime이 없다.
  - 다음 추가는 대형 도구 도입이 아니라 retrieval adapter boundary와 Postgres evidence neighborhood query가 우선이다.
  - AGENTS/roadmap이 정의한 current immediate next task는 변경하지 않는다.
- 이유:
  - 기존 architecture는 deterministic canonical state와 evidence trace를 먼저 안정화하는 흐름이다.
  - AI/RAG를 추천 결정자로 연결하면 감사 가능성과 평가 경계가 깨질 수 있다.
  - tool adoption은 병목이 확인된 뒤 pilot으로 들어가야 한다.

## Exact Next Step

- 다음 세션은 이것부터 시작:
  - `docs/tasks/ai-retrieval-graph-foundation/contract.md`의 Scope와 Mutable Surface를 확인한다.
  - active frontend/API immediate task와 충돌이 없는지 `git status --short`를 확인한다.
  - AI 구현을 진행해야 한다면 `ai-retrieval-adapter-foundation` 같은 별도 task를 먼저 만든다.

## Verification Already Run

- 명령: `rg -n 'Current Implementation Status|ai-retrieval-graph-foundation|Dagster|vector store|ontology-lite|Current task:|현재 고정된 immediate next task' docs/ai-intelligence-architecture.md docs/project-execution-roadmap.md docs/tasks/ai-retrieval-graph-foundation docs/plans/2026-05-03-ai-retrieval-graph-foundation.md AGENTS.md`
- 관찰한 결과: 성공. AI architecture status, roadmap guardrail, task docs, current immediate task 문구가 모두 검색됐다.

- 명령: `git diff --check`
- 관찰한 결과: 성공. whitespace error 없음.

- 명령: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task ai-retrieval-graph-foundation`
- 관찰한 결과: 성공. `Task ai-retrieval-graph-foundation passed readiness checks.`

## Still Unverified

- 항목: real vector retrieval quality
- 왜 중요한가: 아직 vector backend를 선택하거나 runtime query를 구현하지 않았다.

- 항목: graph traversal performance
- 왜 중요한가: 현재는 Postgres graph/evidence neighborhood를 먼저 쓰기로 했고, 복잡도 병목은 아직 측정하지 않았다.

- 항목: orchestration need
- 왜 중요한가: Dagster류 tool은 아직 필요성을 증명하지 않았고, current runner plus `ops.pipeline_run` 패턴을 유지한다.

## Risks

- 위험:
  - 다음 세션이 AI/RAG 작업을 하면서 current immediate frontend/API task를 밀어낼 수 있다.
  - vector DB 또는 graph DB를 너무 빨리 고르면 migration과 운영 비용이 커질 수 있다.
  - ontology validation을 full RDF/SHACL로 바로 키우면 구현 속도가 느려진다.
- 대응:
  - roadmap에 후속 후보로만 적고 current task는 유지한다.
  - 먼저 internal adapter와 SQL validation으로 경계를 고정한다.
  - GraphRAG/Neo4j/RDF는 작은 pilot 조건을 만족할 때만 평가한다.
