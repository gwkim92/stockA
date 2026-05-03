# Frontend API Contract

이 문서는 frontend scaffold 전에 고정하는 read model API contract다. 현재 production API server는 없고, 이 문서와 `docs/api/frontend/` examples가 다음 구현의 기준이다. local fixture HTTP server는 `docs/frontend-fixture-server.md`에 정의되어 있다.

## Contract Version

- version: `frontend-api-v0.1`
- status: draft
- compatibility rule: field 제거 또는 의미 변경은 minor version bump 없이 금지한다.
- system of record: Python/Postgres pipeline.
- frontend consumption: stable DTO, not raw DB tables.

## Common Response Shape

All read responses use this base shape:

```json
{
  "contract_version": "frontend-api-v0.1",
  "generated_at": "2026-05-01T00:00:00Z",
  "data": {},
  "links": {}
}
```

Conventions:

- dates are ISO `YYYY-MM-DD`.
- timestamps are UTC ISO strings.
- decimal ratios use numbers, not percentage strings.
- ids are opaque strings for frontend use.
- `links` contains API paths or UI-adjacent API paths only.
- frontend must not infer raw table names from ids.
- collection responses include top-level `pagination`; detail responses omit it.

## Endpoint Index

Canonical machine-readable index:

- `docs/api/frontend/contract-index.json`

Initial endpoints:

- `GET /api/dashboard/today`: `DailyCockpitResponse`
- `GET /api/remediation-tickets?status=open`: `RemediationTicketsResponse`
- `GET /api/data-health`: `DataHealthResponse`
- `GET /api/cycles?asOfDate=2024-11-01`: `CycleStateListResponse`
- `GET /api/recommendations/AAPL-2024-11-01`: `RecommendationDetailResponse`
- `GET /api/theses/AAPL-bootstrap-v1`: `ThesisDetailResponse`
- `GET /api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01`: `PortfolioCoverageResponse`
- `GET /api/ai-evidence/sec-event-aapl-10k-20240928`: `AiEvidenceDetailResponse`
- `GET /api/source-documents/aapl-2024-10k-20240928`: `SourceDocumentDetailResponse`
- `GET /api/events?asOfDate=2024-11-01`: `EventListResponse`
- `GET /api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01`: `ThemeDetailResponse`
- `GET /api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02`: `PerformanceOutcomesResponse`

Deferred write endpoint:

- `POST /api/remediation-tickets/:id/status`

This write endpoint is deferred until auth, RBAC, actor identity, reason capture, and audit trail are implemented.

## DTO Ownership

Daily cockpit:

- owner route: `/`
- source concepts: pipeline run, remediation report, portfolio coverage, scheduler status.
- example: `docs/api/frontend/examples/daily-cockpit.json`

Remediation tickets:

- owner route: `/remediation`
- source concepts: persistent remediation ticket, source review item, suggested runner.
- example: `docs/api/frontend/examples/remediation-tickets.json`

Data health:

- owner route: `/data-health`
- source concepts: pipeline run history, scheduler gates, artifact roots, data freshness.
- example: `docs/api/frontend/examples/data-health.json`

Cycle state list:

- owner route: `/cycles`
- source concepts: theme, cycle state snapshot, feature values.
- example: `docs/api/frontend/examples/cycle-state-list.json`

Recommendation detail:

- owner route: `/recommendations`
- source concepts: recommendation, score component, thesis, performance outcome, source evidence.
- example: `docs/api/frontend/examples/recommendation-detail.json`

Thesis detail:

- owner route: `/theses`
- source concepts: thesis, invalidation conditions, thesis review, evidence, recommendation.
- example: `docs/api/frontend/examples/thesis-detail.json`

Portfolio coverage:

- owner route: `/portfolio`
- source concepts: position snapshot, active thesis coverage, outcome coverage, attribution readiness.
- example: `docs/api/frontend/examples/portfolio-coverage.json`

AI evidence detail:

- owner route: `/ai-evidence`
- source concepts: model invocation, prompt version, extraction artifact, source chunks, token/cost metadata, quality gate.
- example: `docs/api/frontend/examples/ai-evidence-detail.json`

Source document detail:

- owner route: `/source-documents`
- source concepts: SEC filing metadata, raw artifact storage URI, retrieval run provenance, reviewed excerpts, linked evidence.
- example: `docs/api/frontend/examples/source-document-detail.json`

Event list:

- owner route: `/events`
- source concepts: structured events, theme classification impact, instrument impact, source document linkage, AI evidence linkage.
- example: `docs/api/frontend/examples/event-list.json`

Theme detail:

- owner route: `/themes`
- source concepts: theme cycle state, cycle feature snapshot, linked instruments, supporting events, thesis/recommendation links.
- example: `docs/api/frontend/examples/theme-detail.json`

Performance outcomes:

- owner route: `/performance`
- source concepts: recommendation outcome, thesis outcome, benchmark-relative alpha, attribution component, coverage exclusion.
- example: `docs/api/frontend/examples/performance-outcomes.json`

## Read Boundary

Read APIs should be denormalized for frontend needs.

Rules:

- no frontend query should require joining multiple raw table-shaped endpoints.
- every response includes the minimum evidence links needed for drilldown.
- every risk or action must include a human-readable reason.
- every score-like value must have component or evidence drilldown in detail routes.
- every AI extraction response must expose prompt/model/run metadata and source chunk ids.
- event/theme explorer responses must preserve provenance links instead of presenting cycle state as a standalone buy signal.
- performance responses must distinguish deterministic outcome math from AI narrative and must not hide coverage exclusions.
- raw source documents are not browser-downloadable until auth/RBAC and access policy are implemented.
- live read adapter pilot may serve a subset of read endpoints, but unsupported endpoints must keep fixture fallback or explicit unsupported-path errors rather than exposing raw table-shaped data.

## Write Boundary

Initial frontend release is read-only.

Allowed later:

- remediation ticket status update with actor and reason.
- review note draft save with source evidence ids.
- scheduler setting update only after admin auth.

Disallowed:

- broker order placement.
- direct buy/sell recommendation from chat.
- hidden thesis mutation through AI.
- changing scoring formulas from UI without versioned review.

## API Style

The initial contract is REST resource-oriented.

Rules:

- resources are nouns.
- `GET` endpoints are safe/read-only.
- status mutation uses `POST` or `PATCH` only after audit model exists.
- paginated lists use `limit`, opaque `cursor`, and `next_cursor`, not page numbers, because pipeline data is time ordered.
- invalid pagination returns `FrontendPaginationInvalid`.
- errors should use stable shape: `error.code`, `error.message`, `error.details`, `request_id`.

## Pagination

See `docs/frontend-api-pagination-conventions.md`.

Initial collection endpoints:

- `/api/remediation-tickets?status=open`: `tickets`
- `/api/cycles?asOfDate=...`: `cycle_states`
- `/api/events?asOfDate=...`: `events`
- `/api/portfolio/:portfolio/coverage?asOfDate=...`: `positions`
- `/api/performance/:portfolio/outcomes?measurementEndDate=...`: `outcomes`

Rules:

- default `limit`: `50`
- max `limit`: `100`
- `cursor` is opaque and client must not parse it.
- clients pass `pagination.next_cursor` as the next request's `cursor`.
- detail endpoints reject `limit` or `cursor`.
- collection responses add top-level `pagination` beside `data` and `links`.

## Implementation Status

The read-only Python fixture adapter exists in `src/stockanalysis/frontend/api_adapter.py`, local HTTP fixture serving exists in `src/stockanalysis/frontend/fixture_server.py`, and `apps/web` consumes fixture payloads.

Live read adapter pilot:

- module: `src/stockanalysis/frontend/live_adapter.py`
- CLI: `PYTHONPATH=src python3 -m stockanalysis.frontend.api_adapter get --source live --path "..."`
- supported live endpoints:
  - `GET /api/dashboard/today`
  - `GET /api/data-health`
  - `GET /api/cycles?asOfDate=2024-11-01`
  - `GET /api/events?asOfDate=2024-11-01`
  - `GET /api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01`
  - `GET /api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02`
  - `GET /api/recommendations/AAPL-2024-11-01`
  - `GET /api/theses/AAPL-bootstrap-v1`
  - `GET /api/ai-evidence/sec-event-aapl-10k-20240928`
  - `GET /api/source-documents/aapl-2024-10k-20240928`
  - `GET /api/remediation-tickets?status=open`
  - `GET /api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01`
- source mode: `--source auto` uses live only when `STOCKANALYSIS_PSQL_COMMAND` is configured; otherwise it falls back to fixture examples.

FastAPI read-only server, deployment boundary, and pagination conventions are now defined. SQL-level cursor seek optimization remains a later scaling task.
