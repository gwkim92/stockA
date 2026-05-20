# AI Intelligence Architecture

## Purpose

이 문서는 2026-04-23 기준으로 이 프로젝트에 AI를 어디에, 어떤 방식으로, 어떤 제한 아래 넣을지 고정한다.

핵심 결정은 다음과 같다.

- AI는 최종 추천/매수/매도 결정을 직접 소유하지 않는다.
- AI는 비정형 문서 이해, 이벤트 구조화, thesis 초안, 보유 검토, 리포트 생성, 반대 논리 점검을 담당한다.
- 추천 점수, universe slicing, portfolio constraint, position sizing, 백테스트, 감사 trail은 deterministic code가 담당한다.
- 데이터 구조는 `Postgres canonical state + raw artifact store + AI metadata/audit schema + later vector/graph adapters`로 둔다.

## Current Technology Baseline

2026-04-23 기준 공식 문서와 1차 자료를 확인한 결과, 초기 구현 기준은 아래로 둔다.

- OpenAI API는 신규 AI workflow의 기본 adapter로 `Responses API`를 우선한다. OpenAI 문서는 최신 기능 활용을 위해 Responses API 이전을 권장하고, agent 구축의 미래 방향으로 제시한다.
- 모델 선택은 고정 문자열을 비즈니스 로직에 박지 않고 model gateway에서 관리한다. 2026-04-23 기준 OpenAI 모델 문서는 복잡한 reasoning/coding에 `gpt-5.4`, 비용/지연 최적화에는 `gpt-5.4-mini`, `gpt-5.4-nano`를 제시한다.
- 대량 비동기 추출, classification, embedding backfill은 Batch API 후보로 둔다. 공식 문서 기준 Batch API는 동기 API 대비 비용 할인과 24시간 완료 창을 제공한다.
- 출력은 가능한 한 Structured Outputs 또는 function calling schema로 받는다. 추천/이벤트/thesis 같은 운영 데이터는 자유 텍스트가 아니라 schema validation 가능한 JSON을 먼저 저장한다.
- 검색은 단순 vector RAG만 쓰지 않는다. corpus 전체의 큰 흐름, 테마 연결, second-order effect는 GraphRAG/ontology 계층을 병행해야 한다.

참고한 자료:

- [OpenAI Models](https://developers.openai.com/api/docs/models)
- [OpenAI Responses migration guide](https://developers.openai.com/api/docs/guides/migrate-to-responses)
- [OpenAI Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
- [OpenAI Retrieval and vector stores](https://developers.openai.com/api/docs/guides/retrieval)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAI Function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [OpenAI Batch API](https://developers.openai.com/api/docs/guides/batch)
- [OpenAI Evals](https://developers.openai.com/api/docs/guides/evals)
- [OpenAI Embeddings](https://developers.openai.com/api/docs/guides/embeddings)
- [Microsoft GraphRAG overview](https://microsoft.github.io/graphrag/index/overview/)
- [From Local to Global: A Graph RAG Approach to Query-Focused Summarization](https://arxiv.org/abs/2404.16130)
- [W3C RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/)
- [W3C OWL 2 Overview](https://www.w3.org/TR/owl2-overview/)
- [W3C SHACL](https://www.w3.org/TR/shacl/)

## Where AI Enters

```text
raw data collectors
  -> deterministic normalization
  -> canonical source documents and market data
  -> AI document intelligence
  -> structured events and evidence
  -> theme/sector graph and cycle state
  -> deterministic feature and recommendation scoring
  -> AI thesis, review, report, copilot explanation
```

### 1. Document Intelligence

대상:

- SEC filings
- earnings call transcript
- central bank and government policy documents
- macro reports
- technology/industry reports
- trusted news or analyst notes, if license allows

AI 역할:

- 긴 문서를 section 단위로 읽고 핵심 사건 후보를 추출한다.
- 어떤 문장/문단이 근거인지 evidence pointer를 남긴다.
- 문서 전체 요약이 아니라 투자 판단에 필요한 event, risk, catalyst, invalidation signal을 구조화한다.

저장 위치:

- 원문 메타데이터: `ingest.source_document`
- chunk metadata: `ai.document_chunk`
- model call audit: `ai.model_invocation`
- extraction result: `ai.extraction_artifact`
- canonical event: `event.event`, `event.event_document_link`

### 2. Event Intelligence

첫 번째 AI 런타임 진입점은 `event-intelligence-llm-extract`로 둔다.

이유:

- 이미 `ingest.source_document -> event.event -> event impact` 경로가 있다.
- LLM 결과를 structured event로 저장하면 재처리, 검증, 회귀 테스트가 가능하다.
- 추천을 LLM에 바로 맡기는 것보다 훨씬 안전하다.

필수 output fields:

- event_type
- title
- summary
- event_at
- affected_instruments
- affected_classification_nodes
- impact_direction
- time_horizon
- confidence
- evidence_spans
- uncertainty_notes

### 3. Theme And Sector Mapping

AI는 문서와 이벤트가 어떤 sector/theme node에 연결되는지 제안한다.

최종 writer는 deterministic이어야 한다.

- confidence threshold 미달이면 canonical graph에 반영하지 않는다.
- 신규 theme node 생성은 별도 승인 또는 review queue를 거친다.
- graph edge는 `valid_from`, `valid_to`, source evidence를 가진다.

### 4. Thesis And Review

AI는 아래 텍스트를 만든다.

- long-term thesis draft
- why now
- macro dependency
- technology or regulation driver
- invalidation condition
- opposing view
- hold/reduce/watch review note

하지만 recommendation action과 rank는 deterministic score가 소유한다. AI thesis는 추천을 설명하고 검토하는 증거 layer다.

### 5. Research Copilot

Copilot은 저장된 evidence와 canonical state를 질의한다.

허용 질문:

- 최근 강해지는 테마는 무엇인가
- 특정 종목 thesis가 약해졌는가
- 금리/정책 변화가 어떤 sector에 영향을 주는가
- 내 보유 종목 중 thesis invalidation signal이 있는가

금지 기본값:

- 근거 없는 최신 뉴스 추측
- 저장되지 않은 데이터를 사실처럼 말하기
- portfolio constraint를 무시한 직접 매수/매도 명령

## RAG, GraphRAG, Ontology Decision

결론: `hybrid RAG + ontology/knowledge graph`를 쓴다.

### Current Implementation Status

2026-05-03 기준 현재 상태는 아래처럼 구분한다.

이미 들어간 것:

- `ref.classification_node`, `ref.classification_edge`는 Postgres 기반 ontology-lite graph다.
- `ref.instrument_classification_membership`는 instrument와 classification node의 시간/근거 기반 membership을 저장한다.
- `event.event_classification_impact`와 `event.event_instrument_impact`는 event를 theme/instrument evidence로 연결한다.
- `ai.document_chunk`와 `ai.embedding_index`는 retrieval metadata와 vector storage pointer를 저장한다.
- `ops.pipeline_run`은 deterministic runner provenance를 저장한다.

아직 들어가지 않은 것:

- Dagster, Airflow, Prefect 같은 orchestration framework
- pgvector, OpenAI vector stores, external vector DB 같은 실제 vector retrieval backend
- Neo4j, RDF triple store, OWL/SHACL runtime 같은 full ontology stack
- Microsoft GraphRAG indexing/runtime pipeline

다음 구현 기준:

- 먼저 `ai-retrieval-graph-foundation` task의 contract를 기준으로 internal retrieval adapter와 Postgres evidence neighborhood query를 정의한다.
- production vector DB와 graph DB는 adapter/query 병목이 확인된 뒤 pilot으로 평가한다.
- orchestration framework는 current runner plus `ops.pipeline_run` 패턴이 retry/backfill/dependency visibility를 감당하지 못하는 증거가 있을 때 별도 task에서 평가한다.

### Why Not Plain Vector RAG Only

Vector RAG는 특정 문서/문단을 찾는 데 강하다. 하지만 이 프로젝트의 핵심 질문은 단순 문서 검색이 아니다.

- 여러 문서에 걸친 macro regime 변화
- theme 간 second-order beneficiary
- 정책 변화와 sector cycle의 관계
- 한 종목 thesis가 어떤 upstream/downstream risk에 노출되는지

이런 질문은 관계와 시간축이 필요하다.

### Why Ontology Only Is Not Enough

온톨로지는 entity, relation, constraint를 안정적으로 표현하지만 모든 문서 표현을 즉시 정형화하기 어렵다. 신규 기술 트렌드, 정책 문구, earnings call nuance는 먼저 문서 evidence 검색과 LLM extraction이 필요하다.

### Initial Implementation Shape

초기에는 별도 graph DB를 바로 도입하지 않는다.

- `ref.classification_node`, `ref.classification_edge`를 ontology-lite graph로 사용한다.
- `event.event_*_impact`가 event와 theme/instrument를 연결한다.
- `ai.document_chunk`와 `ai.embedding_index`는 vector index metadata만 저장한다.
- 실제 vector store는 adapter URI로 추상화한다.
- RDF/OWL/SHACL full stack은 export/validation 후보로 두되 MVP 필수 의존성으로 넣지 않는다.

### Later Upgrade Path

- 문서 검색 규모가 커지면 pgvector, OpenAI vector stores, 또는 외부 vector DB adapter를 붙인다.
- graph traversal이 복잡해지면 Neo4j, RDF triple store, 또는 GraphRAG pipeline을 파일럿으로 붙인다.
- ontology 품질 검증이 필요해지면 SHACL-like validation rule을 도입한다.
- GraphRAG는 전체 corpus 질문, community summary, theme map 생성에 우선 적용한다.

## Token And Cost Governance

토큰 절감은 기능이 아니라 architecture requirement다.

### Model Routing

model gateway는 task별 기본 모델을 분리한다.

- cheap extraction/classification: `gpt-5.4-nano` 또는 동급 소형 모델
- normal analyst synthesis: `gpt-5.4-mini` 또는 동급 중간 모델
- high-stakes quarterly review, complex contradiction pass: `gpt-5.4` 또는 더 강한 모델
- embedding: `text-embedding-3-small` 우선, 품질 이슈가 확인되면 `text-embedding-3-large`

모델명은 config에서 관리한다. code path는 `task_name`, `provider`, `model_name`, `reasoning_effort`만 기록한다.

### Prompt Caching

고정 system prompt, output schema, tool schema, investment policy는 prompt 앞부분에 둔다.

기록할 값:

- input_token_count
- output_token_count
- cached_input_token_count
- latency_ms
- estimated_cost_usd

이 값들은 `ai.model_invocation`에 저장해 task별 캐시 효율과 비용을 추적한다.

### Batch Processing

즉시 응답이 필요 없는 작업은 Batch API 또는 동등한 비동기 provider adapter를 사용한다.

대상:

- historical SEC filing extraction
- earnings transcript backlog extraction
- theme mapping backfill
- embedding backfill
- eval dataset run

### Context Minimization

LLM 입력에는 전체 원문을 넣지 않는다.

- chunk id
- short evidence quote or excerpt
- document metadata
- already extracted event summary
- delta since last review
- relevant graph neighborhood

만 보낸다.

### Reuse Extracted Artifacts

한 번 추출한 event/thesis/evidence는 다시 원문을 읽지 않도록 저장한다.

- source document checksum이 바뀌지 않았다면 재추출하지 않는다.
- prompt_template version 또는 output_schema version이 바뀐 경우에만 backfill 후보로 둔다.
- recommendation/review는 raw filing 대신 structured event와 thesis state를 우선 읽는다.

### Escalation Rules

작은 모델 결과를 항상 큰 모델로 재검토하지 않는다.

큰 모델 escalation 조건:

- confidence threshold 미달
- affected instrument가 portfolio holding
- event significance high
- conflicting evidence exists
- thesis invalidation candidate
- eval failure bucket에 해당하는 event type

## Data Management

### Source Of Truth

- canonical operational state: Postgres
- raw text/PDF/HTML: raw artifact store path
- large research matrices: Parquet + DuckDB
- vector payload: vector store adapter
- model audit and extraction metadata: `ai` schema

### New `ai` Schema

`db/migrations/0005_ai_intelligence.sql`은 아래 boundary를 만든다.

- `ai.prompt_template`: prompt, template version, output schema
- `ai.model_invocation`: provider/model/token/cost/status audit
- `ai.document_chunk`: source document chunk metadata and preview
- `ai.embedding_index`: embedding metadata and vector storage pointer
- `ai.extraction_artifact`: structured LLM output before/alongside canonical writes
- `ai.eval_run`: prompt/model/dataset evaluation results

Postgres에는 full raw document body를 저장하지 않는다. Postgres에는 chunk metadata, preview, hash, pointer만 둔다.

### Versioning Rules

반드시 versioned로 저장할 것:

- prompt template
- output JSON schema
- model name and provider
- extraction code version
- source document checksum
- eval dataset version
- graph taxonomy version, when introduced

## Quality Gates

### Structured Outputs First

AI output은 운영 테이블에 바로 쓰지 않는다.

1. LLM이 schema-constrained artifact를 생성한다.
2. application validator가 JSON schema, required fields, enum, confidence를 검증한다.
3. deterministic writer가 canonical tables에 반영한다.
4. extraction artifact와 canonical row를 provenance로 연결한다.

### Evidence Required

투자 관련 AI output은 evidence 없이 저장하지 않는다.

필수:

- source_document_id
- chunk_id or evidence span
- confidence
- uncertainty_notes
- prompt_template_id
- invocation_id

### Contradiction Pass

thesis와 보유 검토에는 반대 논리 pass를 둔다.

- thesis를 강화하는 evidence
- thesis를 약화하는 evidence
- 아직 판단할 수 없는 unknown
- invalidation condition hit 여부

### Evals

초기 eval set은 fixture 기반으로 만든다.

- SEC filing event extraction golden set
- event-to-theme mapping golden set
- thesis review golden set
- no-evidence refusal set
- hallucination regression set

Evals 결과는 `ai.eval_run`에 저장한다.

## Immediate Next Implementation

다음 AI 구현은 `event-intelligence-llm-extract`가 적절하다.

작업 순서:

1. fixture provider로 `ai.prompt_template`, `ai.document_chunk`, `ai.model_invocation`, `ai.extraction_artifact`, canonical `event.event` write path를 먼저 검증한다.
2. SEC raw filing artifact에서 bounded chunk를 읽는다.
3. Structured Outputs schema로 event candidate를 생성한다.
4. confidence/evidence validation을 통과한 candidate만 `event.event`로 canonical upsert한다.
5. fixture golden set으로 integration verify를 만든다.
6. 그 다음 live OpenAI Responses API adapter와 retry/rate-limit policy를 별도 task로 붙인다.

## Non-Goals

- 실거래 자동화
- LLM 직접 position sizing
- LLM 직접 recommendation rank 결정
- 처음부터 full ontology/triple store 도입
- 처음부터 모든 뉴스/소셜 미디어 수집
- license가 불명확한 문서 본문 저장

## Current Open Risks

- 최신 모델과 가격은 provider가 바꿀 수 있으므로 model gateway config와 문서 주기적 갱신이 필요하다.
- GraphRAG는 비용이 큰 indexing 단계가 있으므로 전체 corpus 도입 전에 작은 sector/theme corpus로 파일럿해야 한다.
- ontology를 너무 빨리 정교화하면 구현 속도가 느려질 수 있다. 초기에는 Postgres graph tables와 명시적 relation type으로 충분하다.
- AI output이 좋아 보여도 evidence, schema validation, eval이 없으면 canonical decision에 반영하면 안 된다.
