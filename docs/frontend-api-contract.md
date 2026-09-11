# Frontend API Contract

이 문서는 Python/Postgres의 읽기 모델을 웹에 전달하는 API contract다. 현재 운영 API와 local fixture HTTP server가 있으며, 초기 examples는 저장된 계약 예시다. 운영 배포 상태는 최신 task handoff와 실제 조회로 확인한다. local fixture HTTP server는 `docs/frontend-fixture-server.md`에 정의되어 있다.

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
- `GET /api/stocks`: `StockListResponse`
- `GET /api/stocks/AAPL`: `StockDetailResponse`
- `GET /api/paper-trading/preview`: `PaperTradingPreviewResponse`
- `GET /api/trading/readiness`: `TradingReadinessResponse`
- `GET /api/cycles?asOfDate=2024-11-01`: `CycleStateListResponse`
- `GET /api/cycle-map?asOfDate=2026-06-05`: `CycleMapResponse`
- `GET /api/market-map?asOfDate=2026-06-05`: `MarketMapResponse`
- `GET /api/recommendations`: `RecommendationListResponse`
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
- source concepts: pipeline run history, expected operation cadence, job health status, scheduler activation approval gate, manual local ingest smoke summary, local ingest worker summary, artifact roots, data freshness, free-tier provider budget ledger status, and the additive recommendation-weight readiness semantics v2 shadow artifact.
- shadow boundary: `recommendation_weight_review_readiness_semantics_v2` is non-authoritative visibility only. It separates evidence, read-only review eligibility, explicit authorization, pilot state, and mutation boundaries without feeding the existing readiness, outcome-router, open-gate, scoring, portfolio, or order decisions. `threshold_evidence_ready=true` does not make `manual_review_eligible=true`: stable row identity, feedback deduplication, versioned component snapshots, an approved horizon policy, and an approved freshness policy must all be attested first.
- projection boundary: the API reconstructs an exact nested allowlist. Raw nested authorization, pilot, mutation, order, and broker keys are discarded, while the exposed authorization/pilot/mutation fields are fixed to the read-only blocked state.
- example: `docs/api/frontend/examples/data-health.json` is illustrative and may omit this additive sibling; clients must use the documented fail-closed default when it is absent.

Stock list:

- owner route: `/stocks`
- source concepts: instrument, daily price bars, latest recommendation, latest position snapshot.
- example: `docs/api/frontend/examples/stock-list.json`

Stock detail:

- owner route: `/stocks/[symbol]`
- source concepts: instrument, bounded price bars for charting, latest recommendation, latest position snapshot, recent linked events.
- example: `docs/api/frontend/examples/stock-detail.json`

Paper trading preview:

- owner route: `/paper-trading`
- source concepts: latest recommendation batch, latest paper portfolio snapshot, recommendation outcomes, simulated paper action candidates, human approval guardrails.
- example: `docs/api/frontend/examples/paper-trading-preview.json`
- boundary: read-only preview only; no broker API, account permission, order transmission, ledger write, or automatic approval.

Trading readiness:

- owner route: `/trading-readiness`
- source concepts: broker boundary, account permission, order limit policy, kill switch, paper validation run, order intent audit summary.
- example: `docs/api/frontend/examples/trading-readiness.json`
- boundary: read-only readiness only; no broker secret value, order write API, fill ingestion, or broker submission.

Cycle state list:

- owner route: `/cycles`
- source concepts: theme, cycle state snapshot, feature values.
- example: `docs/api/frontend/examples/cycle-state-list.json`

Cycle map:

- owner route: `/cycle-map`
- source concepts: classification node/edge hierarchy, hierarchical cycle snapshot, direct event impact, propagated instrument impact, recommendation and thesis linkage.
- example: `docs/api/frontend/examples/cycle-map.json`
- boundary: read-only context map only; it explains where evidence flows, but does not submit orders or mutate recommendation weights.

Market map:

- owner route: `/market-map`
- source concepts: cross-asset indicator observations, indicator snapshots, regime snapshots, data freshness flags, news-indicator linkage.
- example: `docs/api/frontend/examples/market-map.json`
- boundary: read-only cross-asset context only; stale indicators are not imputed.

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

Current enforcement:

- `apps/web` exposes no Server Action or browser-side write proxy.
- internal Codex OAuth relogin and smoke operations remain out-of-band server CLI/SSH actions and must not be proxied with server-held admin tokens.
- browser view models use explicit allowlists and exclude one-time auth data, process ids, filesystem paths, and raw diagnostic strings.

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
- `/api/stocks`: `stocks`
- `/api/paper-trading/preview`: `paper_actions`
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
- `GET /api/cycle-map?asOfDate=2026-06-05`
- `GET /api/market-map?asOfDate=2026-06-05`
- `GET /api/events?asOfDate=2024-11-01`
  - `GET /api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01`
  - `GET /api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02`
  - `GET /api/recommendations/AAPL-2024-11-01`
  - `GET /api/theses/AAPL-bootstrap-v1`
  - `GET /api/ai-evidence/sec-event-aapl-10k-20240928`
  - `GET /api/source-documents/aapl-2024-10k-20240928`
  - `GET /api/remediation-tickets?status=open`
  - `GET /api/portfolio/Long%20Term%20Paper/coverage?asOfDate=2024-11-01`
  - `GET /api/stocks`
  - `GET /api/stocks/AAPL`
  - `GET /api/paper-trading/preview`
  - `GET /api/trading/readiness`
- source mode: `--source auto` uses live only when `STOCKANALYSIS_PSQL_COMMAND` is configured; otherwise it falls back to fixture examples.

FastAPI read-only server, deployment boundary, and pagination conventions are now defined. SQL-level cursor seek optimization remains a later scaling task.

## 2026-09-11 판단 상태와 리서치 근거 보정

`purpose-fit-recovery-20260911`은 잘못된 대체값과 목록/상세의 불일치를 수정한다. 실제 운영 반영 여부는 해당 task handoff를 확인한다.

- `decision_boundary.paper_validation_input_allowed`는 가상 검증에 필요한 thesis·점수·뉴스/AI 입력과 원천 차단 여부로 정한다. 성과 측정 완료를 의미하지 않으며, 목록·상세는 동일 정책을 사용한다. 전문 내용 검토·투자 판단 채택·주문은 별도다. `paper_validation_pending`에서도 입력은 가능할 수 있다.
- 기업/추천 `equity_research.generation`은 `mode` (`ai`/`fallback`/`unknown`), `structural_status`, `content_review_status`, `source_document_count`, `source_scope`를 추가한다. 필수 자료형 충족은 내용 검증이 아니며 원천 문서 연결은 주장별 입증이 아니다. 내용 검토 저장 기록이 없으면 `not_recorded`다.
- 가격 `freshness_policy=calendar_age_within_7_days`와 `freshness_age_days`는 기존 7일 수집 시차 판정의 의미를 드러낸다. `fresh`는 실시간 가격 판정이 아니다. 명시적인 최신성 정보 없이 가격 행만 있으면 `unknown`이다.
- 사이클·테마의 `features.market_breadth`, `features.valuation_score`는 각각 독립 지표다. 직접적인 재무 품질 측정이 없을 때 `fundamental_quality`는 null이며 다른 지표를 대신 넣지 않는다.

## Stored recommendation outcome explorer (2026-09-11)

`GET /api/recommendation-outcomes` is an additional live-only, authenticated read endpoint, version `recommendation-outcome-explorer-v1`. It reads all stored `performance.recommendation_outcome` measurements without requiring portfolio positions or attribution reports. The existing `/api/performance/outcomes` and its v0.1 DTO remain unchanged.

Optional query parameters: `symbol` (case-insensitive exact code), `from_date`/`to_date` (inclusive recommendation dates), `horizon` (`30`, `90`, `180`, `365`, `other`), `benchmark` (exact case-insensitive code; `_missing` means NULL), `alpha` (`positive`, `negative`, `zero`, `missing`), `before` (`YYYY-MM-DD:outcome_id`), `through` (inclusive outcome ID ceiling), and `limit` (1–100, default 25). Duplicated/unknown parameters and malformed values return 400. Existing read-token and method restrictions apply. Query failures and fixture-only mode return 503 rather than fabricated empty results.

The response carries `filters`, whole-filtered-scope `summary` counts and recommendation date bounds, global `benchmarks`, `rows`, and `pagination`. Rows contain stored returns, prices, benchmark, alpha, actual observation dates/days, nominal horizon, current recommendation metadata, and an optional latest matching recommendation evaluation snapshot. IDs are decimal strings. Missing numeric values remain NULL and zero remains zero. No mixed-horizon or mixed-benchmark return average is calculated.

Rows are ordered by measurement end date descending, then outcome ID descending. Carry `next_cursor` as `before` and `through` on continuation requests to exclude newly inserted records, including backfills. Reload without both to include new records. This bounds insert visibility; it is not a historical transaction snapshot and does not freeze later corrections to existing rows. Summary counts span the complete filter scope at the selected ceiling, not just the page.

The nominal horizon reuses the existing evaluation helper (30/90/180/365 days, ±7 days); actual dates and days remain visible and all other measurements remain queryable. Recommendation/thesis links refer to current stored records. `evaluation_snapshot` selects only the recommendation calibration family with matching source recommendation and outcome IDs. It is an evaluation-time preservation record, not an immutable recommendation-creation snapshot.
