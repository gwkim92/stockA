# AI Role Map

이 프로젝트에서 AI는 추천 결정을 직접 내리는 주체가 아니다. AI는 비정형 정보를 구조화하고, 투자 thesis와 검토 리포트를 생성하며, 사람이 이해할 수 있는 설명을 만드는 intelligence layer다.

상세 architecture, token/cost governance, RAG와 ontology 병행 전략은 `docs/ai-intelligence-architecture.md`를 기준으로 한다.

## Core Principle

- deterministic code owns: ingestion, normalization, schema validation, scoring, ranking, portfolio constraints, audit trails
- AI owns: document understanding, event extraction, thesis drafting, contradiction checking, narrative reporting, analyst copilot UX

즉 AI output은 저장되고 검증 가능한 evidence가 되어야 한다. AI가 근거 없이 최종 매수/매도 결정을 생성하면 안 된다.

## Where AI Enters

### 1. Event Intelligence

AI는 뉴스, 공시, 정책 문서, 실적 발표, 산업 리포트를 읽고 structured event로 바꾼다.

- event type
- affected sector/theme/instrument
- polarity
- time horizon
- confidence
- evidence summary
- source document links

현재 SEC event extraction은 heuristic bootstrap이다. 후속 단계에서 LLM extraction을 붙일 수 있는 위치가 여기다.

### 2. Theme And Sector Mapping

AI는 문서나 산업 변화가 어떤 theme/sector node와 연결되는지 판단하는 보조 역할을 한다.

- direct theme impact
- second-order beneficiary
- regulatory risk
- supply-chain linkage
- uncertainty notes

다만 최종 graph update는 confidence, source, version을 남기는 deterministic writer를 거쳐야 한다.

### 3. Thesis Engine

AI는 종목별 투자 thesis 초안을 만든다.

- why now
- core growth driver
- macro dependency
- invalidation condition
- expected holding period
- key risks
- opposing view

하지만 thesis 생성은 추천과 다르다. recommendation engine은 별도 점수와 risk rule을 사용해야 한다.

### 4. Portfolio Review

AI는 보유 종목의 thesis가 유지되는지 검토하는 리포트를 만든다.

- original thesis vs new evidence
- strengthened/weakened/unchanged
- what changed since entry
- whether price move matches thesis
- risk events to monitor

이 검토는 portfolio engine의 deterministic metrics와 event history를 읽어 설명하는 역할이다.

### 5. Research Copilot

AI는 사용자가 질문할 때 저장된 데이터와 이벤트를 기반으로 답한다.

- 최근 강해진 theme은 무엇인가
- 어떤 보유 종목의 thesis가 약해졌는가
- 특정 거시 변화가 어떤 섹터에 영향을 주는가
- 추천 후보의 반대 논리는 무엇인가

Copilot은 데이터베이스와 evidence store 위에서 답해야 하며, 임의 추측을 기본값으로 삼으면 안 된다.

## Where AI Must Not Own The Decision

- canonical data ingestion
- price/fundamental/macro upsert
- schema migration
- universe slicing
- raw ranking score
- position sizing
- risk limit
- trade execution

이 영역은 reproducibility와 auditability가 더 중요하다.

## Near-Term AI Integration Point

가장 먼저 AI를 붙일 위치는 `event-intelligence-llm-extract`다.

이유:

- 이미 `ingest.source_document`, `event.event`, `event.event_document_link`, `event.event_classification_impact`, `event.event_instrument_impact` 경로가 있다.
- AI output이 structured event로 저장되므로 검증과 재처리가 가능하다.
- 추천 로직에 직접 AI를 넣는 것보다 리스크가 낮다.

이 구현은 아래 boundary를 지켜야 한다.

- model gateway가 provider, model, reasoning effort를 결정한다.
- raw document 전체를 매번 LLM에 보내지 않고 bounded chunk와 evidence candidate만 보낸다.
- Structured Outputs 또는 function calling schema를 사용한다.
- 모든 model call은 `ai.model_invocation`에 token, cost, latency, status와 함께 남긴다.
- LLM의 raw output은 먼저 `ai.extraction_artifact`에 저장하고, validator를 통과한 결과만 canonical `event.*` tables에 반영한다.

## Long-Term Flow

```text
documents -> AI event extraction -> event graph -> cycle state -> thesis draft -> deterministic recommendation score -> AI explanation/report
```

AI는 앞단에서 비정형 정보를 구조화하고, 뒷단에서 설명과 검토를 만든다. 중간의 점수화와 포트폴리오 결정은 검증 가능한 deterministic engine이 맡는다.
