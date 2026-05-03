# Project Execution Roadmap

이 문서는 2026-05-01 기준으로 프로젝트의 현재 위치, 흔들리지 않을 진행 순서, 각 순서의 근거를 고정한다.

## Purpose

프로젝트 목적은 단순 종목 추천 앱이 아니라 거시경제, 정치, 기술, 산업, 기업 흐름을 지속적으로 해석하고 섹터/테마 사이클을 추적하여 중장기 투자 thesis, 추천, 보유 검토, 성과 분석을 지원하는 AI 기반 투자 운영 시스템을 만드는 것이다.

## Current State

현재 저장소는 초기 설계만 있는 상태가 아니다. 다음 기반은 이미 있다.

- Postgres canonical schema: `db/migrations/0001_bootstrap.sql`부터 `0012_portfolio_remediation_ticket.sql`.
- 데이터 수집/정규화: macro FRED, SEC filings/companyfacts/raw filing, Alpha Vantage price, universe bootstrap.
- signal pipeline: strategy universe, market feature, theme enrichment, cycle state, recommendation, score component, thesis, thesis review.
- portfolio pipeline: position snapshot, portfolio review, remediation queue/ticket/update/daily runner, scheduler wrapper.
- performance pipeline: recommendation/thesis outcome, scheduled outcome runner, attribution, outcome coverage.
- AI foundation: `ai` schema, model invocation/chunk/embedding/extraction/eval metadata, SEC event structured extraction fixture path.
- frontend contract/runtime: 12개 DTO contract, fixture server, initial live read adapter completeness, `--source fixture|live|auto`, runtime boundary policy, actual DB-backed HTTP live smoke, FastAPI read-only API server with psycopg pool, request id/timeout/structured log/readiness hardening, deployment boundary/env preflight, pagination conventions, Next.js read-only cockpit routes.
- harness: task contract/plan/handoff/review directories and verification scripts.

## Not Done

아래는 아직 끝나지 않았다.

- actual managed deployment install, reverse proxy config, optional OTLP exporter runtime, SQL-level pagination optimization.
- full auth/RBAC, actor identity, audit-enforced write APIs.
- actual recurring production data jobs with real credentials and alerting.
- broad AI provider gateway, model routing, vector/RAG runtime, eval pipeline.
- recommendation quality evaluation beyond deterministic bootstrap fixtures.
- real brokerage/order integration. This remains out of scope until separately approved.

## Execution Order

### 1. Live Read Completeness

Goal: frontend DTO contract를 fixture가 아니라 canonical Postgres state에서 읽을 수 있게 만든다.

Why first:

- 프론트 확장보다 데이터 truth boundary가 먼저다.
- 이미 local runtime과 live adapter pilot이 있으므로 가장 가까운 병목이다.
- live read가 완성되어야 dashboard, data health, AI evidence, performance 화면이 실제 운영 가치를 가진다.

Initial scope:

- Expand live reads for `/api/dashboard/today`. First slice implemented in `frontend-live-read-expansion`.
- Expand live reads for `/api/data-health`. First slice implemented in `frontend-live-read-expansion`.
- Expand live reads for `/api/events?asOfDate=...`. Second slice implemented in `frontend-live-read-event-theme-performance`.
- Expand live reads for `/api/themes/:themeKey?asOfDate=...`. Second slice implemented in `frontend-live-read-event-theme-performance`.
- Expand live reads for `/api/performance/:portfolio/outcomes?...`. Second slice implemented in `frontend-live-read-event-theme-performance`.
- Expand live reads for recommendation/thesis/AI evidence/source document detail. Third slice implemented in `frontend-live-read-detail-endpoints`.
- Expand live reads for `/api/cycles?asOfDate=...`. Fourth slice implemented in `frontend-live-read-cycle-list`.
- Remaining live read gap: none for the initial frontend contract endpoints.

Guardrail:

- DTO contract는 유지한다.
- DB schema, benchmark, scoring formula는 이 단계에서 바꾸지 않는다.
- unsupported endpoints must return fixture fallback in `auto`, not raw tables.

### 2. API Runtime Boundary

Goal: local runtime을 production API 후보 구조로 승격할지, 별도 server를 도입할지 결정하고 구현한다.

Why second:

- live read model이 충분하지 않은 상태에서 API framework를 먼저 키우면 껍데기만 커진다.
- auth/RBAC와 write APIs는 runtime boundary가 안정된 뒤에만 의미가 있다.

Initial scope:

- Add local/production runtime profile and startup guard. Implemented in `frontend-api-runtime-boundary`.
- Add read-token auth seam and explicit CORS boundary. Implemented in `frontend-api-runtime-boundary`.
- Keep write endpoints blocked until full auth/RBAC exists.
- Add actual DB-backed HTTP live success smoke. Implemented in `frontend-runtime-db-smoke`.
- Decide Python API server framework and connection pooling. Implemented in `frontend-api-server-framework-decision`.
- Add stable request id, timeouts, readiness probes, and structured logs. Implemented in `frontend-api-server-observability-hardening`.
- Add deployment topology, loopback process boundary, reverse proxy/TLS assumptions, and repo-outside runtime env preflight. Implemented in `frontend-api-server-deployment-boundary`.
- Add list endpoint `limit`, opaque `cursor`, and `next_cursor` conventions. Implemented in `frontend-api-pagination-conventions`.
- Decide external metrics/log sink and alerting boundary. Implemented in `frontend-api-observability-sink-decision`.
- Later: optional OTLP exporter pilot and SQL-level pagination optimization.

Guardrail:

- no write endpoint before auth/RBAC.
- no database credentials in browser or Next bundle.

### 3. Data Operations Loop

Goal: 수집/정규화/신호/리뷰/성과 파이프라인을 일회성 검증에서 반복 가능한 운영 루프로 만든다.

Why third:

- long-term investment system은 freshness와 rerun provenance가 핵심이다.
- scheduler wrapper는 있으나 full data operations dashboard와 failure recovery loop는 아직 약하다.

Initial scope:

- define daily/weekly/monthly job cadence.
- connect failed/stale/missing runs to data-health live read.
- persist run artifacts and stdout/stderr locations consistently.
- document runtime env readiness for each data source.

Guardrail:

- secrets remain outside repo.
- real credentials are opt-in runtime config, never committed.

### 4. AI Runtime

Goal: AI를 provider gateway, structured output validation, retrieval, cost logging, eval로 운영 가능한 계층으로 만든다.

Why fourth:

- AI는 canonical data와 evidence graph 위에서 동작해야 한다.
- AI를 먼저 키우면 추천 책임과 증거 책임이 섞인다.

Initial scope:

- model gateway with task-based routing.
- structured output validators.
- prompt template versioning and model invocation logging.
- document chunking and embedding adapter.
- Postgres evidence neighborhood query before graph DB adoption.
- retrieval adapter boundary before production vector store selection.
- eval dataset for event extraction and thesis review quality.

Guardrail:

- AI does not directly own buy/sell/rank decisions.
- deterministic scoring remains source of recommendation action.
- `ai-retrieval-graph-foundation` captures the handoff for RAG/ontology/graph work; it is a future AI Runtime task and does not replace the current immediate task.
- Do not add Dagster/Prefect/Airflow, Neo4j/RDF/GraphRAG, or production vector DB until a task contract proves the current adapter/runner approach is insufficient.

### 5. Recommendation And Cycle Quality

Goal: bootstrap score를 넘어 중장기 추천 품질을 평가 가능한 형태로 고도화한다.

Why fifth:

- score 고도화는 데이터, live read, AI evidence, performance feedback loop가 붙은 뒤 해야 한다.
- 섣부른 formula 변경은 benchmark/evaluation drift를 만든다.

Initial scope:

- expand universe coverage.
- add cycle features and theme breadth.
- define backtest/evaluation split.
- compare recommendation outcomes by horizon and theme.

Guardrail:

- benchmark, evaluation split, scoring formula changes require explicit task contract.

### 6. Frontend Productization

Goal: live backend 기반 cockpit을 실제 운영 UI로 만든다.

Why sixth:

- UI는 already exists, but should not lead the architecture.
- live data and API boundaries must stabilize before complex interaction work.

Initial scope:

- connect routes to live/auto backend.
- add filtering, pagination, and table fallback.
- add accessibility audit.
- add settings/admin only after auth/RBAC.

Guardrail:

- no broker/order flow.
- no hidden thesis mutation from UI.
- no direct AI buy/sell chat.

## Immediate Next Task

Current task: `frontend-api-otel-exporter-pilot`.

The first implementation expanded live read support, not new frontend pages. It started with `dashboard` and `data-health`, then event/theme/performance, then recommendation/thesis/AI evidence/source document detail, then cycle list. Initial frontend contract live read completeness is covered. Runtime boundary policy, DB-backed HTTP live smoke, FastAPI read-only server, API observability hardening, deployment boundary, pagination conventions, and external observability sink decision are now in place; next work should pilot optional OTLP export before write APIs or frontend product expansion.

## Focus Rules

- If a task does not improve live data truth, runtime safety, AI evidence quality, recommendation evaluation, or operator visibility, it is lower priority.
- If a task changes benchmark, schema, scoring, or auth boundary, it needs explicit task contract and verification.
- If frontend work is requested before live read completion, keep it limited to consuming existing DTOs unless explicitly approved.
- If AI work is requested before model gateway/eval exists, implement gateway/eval first rather than prompt-only features.
