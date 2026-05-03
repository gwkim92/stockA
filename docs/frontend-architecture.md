# Frontend Architecture

현재 이 프로젝트에는 fixture-only frontend app scaffold가 있다. 지금까지의 core 구현은 `src/stockanalysis/ingest/`, Postgres schema, CLI runner, scheduler wrapper, verification script 중심이고, `apps/web`은 read-only cockpit shell로 시작한다.

frontend는 단순 종목 추천 화면이 아니라 **investment cockpit**이어야 한다. 사용자는 AI가 뽑은 단일 답을 소비하는 것이 아니라, cycle, theme, thesis, portfolio review, remediation ticket, performance outcome, source evidence를 한 화면 흐름에서 검토해야 한다.

## Current Decision

- frontend scaffold는 `apps/web`에 만들었다.
- 첫 frontend task는 `apps/web` 생성이 아니라 API contract와 read model 정의였고, 현재 `docs/frontend-api-contract.md`와 `docs/api/frontend/` examples로 초안이 고정됐다.
- local fixture HTTP server가 있고 `apps/web`은 browser-facing route shell에서 fixture payload를 읽는다.
- live Postgres read adapter pilot이 있고 remediation tickets와 portfolio coverage DTO를 canonical reports에서 변환한다.
- local frontend API runtime은 `--source fixture|live|auto`로 시작할 수 있다.
- runtime boundary policy는 local/prod profile, CORS, read-token auth seam, non-loopback startup guard를 적용한다.
- frontend는 Python/Postgres pipeline을 대체하지 않는다.
- browser는 DB에 직접 연결하지 않는다.
- LLM은 frontend에서 추천을 직접 결정하지 않는다.

## Proposed Stack

- Web app: `apps/web` with Next.js App Router and TypeScript.
- Rendering model: React Server Components by default, Client Components only for filters, charts, tables, keyboard interactions, and live polling.
- Backend boundary: Python API adapter owns SQL/read models and job commands. Next.js may provide a Backend-for-Frontend layer for auth/session/UI-specific composition, but should not duplicate core scoring SQL.
- Server state: server-rendered snapshots first; TanStack Query only where client-side refresh, polling, optimistic interaction, or long-running job status needs it.
- Styling: repo-local design tokens, accessible components, dense information layout. Avoid generic template dashboards.

Rationale:

- Next.js App Router is file-system based and integrates React Server Components, Suspense, and Server Functions: https://en.nextjs.im/docs/app/
- React Server Components render before bundling and can reduce client-side bundle/data-fetch overhead for server-owned data views: https://react.dev/reference/rsc/server-components
- Next.js Route Handlers can support a Backend-for-Frontend pattern, but Server Components should fetch directly from the underlying source instead of calling route handlers when possible: https://nextjs.org/docs/app/guides/backend-for-frontend
- TanStack Query is useful for client-side server state when the UI needs refresh, polling, or mutation flows: https://tanstack.com/query/latest

## Product Shape

The UI should feel like an operating room for long-term investing, not a retail brokerage clone.

Primary users:

- portfolio operator reviewing daily remediation.
- research operator validating theme/cycle changes.
- thesis owner checking invalidation and evidence drift.
- performance reviewer comparing recommendation outcomes against thesis and benchmark.

Primary jobs:

- See what changed since the last run.
- Understand why a theme, thesis, or position needs attention.
- Trace each recommendation to source documents, event impacts, cycle state, score components, and thesis.
- Track whether past recommendations performed as expected.
- Decide the next manual action: monitor, refresh thesis, update position link, investigate missing outcome, or ignore with reason.

## Route Map

Initial route set:

- `/`: Daily cockpit with run status, open remediation tickets, critical blind spots, latest pipeline failures.
- `/cycles`: Sector/theme cycle map, state transitions, cycle confidence, feature snapshots.
- `/themes/[themeKey]`: Theme detail, linked instruments, events, cycle history, score components.
- `/recommendations`: Recommendation batches, score components, thesis links, outcome status.
- `/theses`: Active thesis library, invalidation conditions, review history, missing coverage.
- `/portfolio`: Position snapshots, thesis coverage, outcome coverage, exposure, cash weight.
- `/remediation`: Persistent remediation tickets, status workflow, suggested runner, source review item.
- `/performance`: Recommendation/thesis outcomes, attribution components, benchmark-relative performance.
- `/events`: SEC/news/macro events, classification/instrument impact, source documents.
- `/data-health`: Pipeline runs, stale data, missing filings, failed runners, scheduler artifacts.
- `/ai-evidence`: Structured AI extraction outputs, confidence, source chunks, provenance, token/cost metadata.
- `/settings`: Runtime env readiness, scheduler status, skip dates, artifact retention, alert destination once implemented.

## Data Boundary

Frontend must consume stable read models, not raw operational tables.

Recommended API shape:

- `GET /api/dashboard/today`
- `GET /api/pipeline-runs?limit=...`
- `GET /api/cycles?asOfDate=...`
- `GET /api/themes/:themeKey`
- `GET /api/recommendations?batchDate=...`
- `GET /api/theses?status=active`
- `GET /api/portfolio/:portfolioName/review?asOfDate=...`
- `GET /api/remediation-tickets?status=open`
- `POST /api/remediation-tickets/:id/status`
- `GET /api/performance/outcomes?...`
- `GET /api/events?...`
- `GET /api/source-documents/:id`
- `GET /api/ai-runs/:runId`

Read/write split:

- read APIs return denormalized DTOs with stable names.
- write APIs are narrow command adapters over existing audited operations.
- status-changing APIs must require reason, actor, and source run id when relevant.
- long-running jobs should return job ids and be polled from `/data-health` or `/settings`.

## AI Boundary

AI in frontend should support interpretation, not autonomous trade/recommendation decisions.

Allowed AI surfaces:

- explain a thesis using already stored evidence.
- summarize why a remediation ticket exists.
- compare current thesis against invalidation conditions.
- draft a review note with citations to stored source documents.
- generate a daily operator report from persisted pipeline outputs.

Disallowed until separately approved:

- direct buy/sell recommendation generation from chat.
- broker order placement.
- silent thesis changes.
- hidden prompt-only scoring changes.
- using browser-side secrets for model calls.

Token/cost controls:

- frontend sends ids, filters, and requested report type, not large raw context.
- backend retrieves curated evidence chunks.
- generated summaries are stored with prompt version, source ids, model id, token counts, and run id.
- default UI should show deterministic pipeline outputs first, AI narrative second.

## Security Boundary

- read-only first release.
- authentication required before any non-local deployment.
- role-based permissions: viewer, analyst, operator, admin.
- no database credentials in browser.
- no API keys in frontend bundle.
- all ticket status changes and generated notes require audit trail.
- raw source documents may need access controls before user/team expansion.

## UX Direction

Visual direction:

- dense but calm cockpit, optimized for scanning risk and evidence.
- avoid purple SaaS dashboard defaults.
- use a restrained palette: paper background, ink text, amber risk, blue evidence, green validated, red broken thesis.
- first screen answers: what changed, what is broken, what needs human action, what evidence supports it.

Interaction principles:

- every score links to components.
- every AI summary links to source evidence.
- every remediation ticket links to the originating review item and pipeline run.
- every chart has table fallback and exportable data.
- default sort favors risk and missing coverage, not highest return.

## Implementation Phases

Phase 0: current task

- frontend architecture documented.
- superseded by fixture-only app scaffold.

Phase 1: API contract foundation

- status: documented as `docs/frontend-api-contract.md`.
- DTO examples: `docs/api/frontend/examples/`.
- verification: `scripts/verify_frontend_api_contract.sh`.

Phase 1.5: API adapter foundation

- status: read-only fixture adapter documented as `docs/frontend-api-adapter.md`.
- module: `src/stockanalysis/frontend/api_adapter.py`.
- verification: `scripts/verify_frontend_api_adapter.sh`.

Phase 1.6: Fixture server foundation

- status: local read-only fixture HTTP server documented as `docs/frontend-fixture-server.md`.
- module: `src/stockanalysis/frontend/fixture_server.py`.
- verification: `scripts/verify_frontend_fixture_server.sh`.

Phase 1.7: Live read adapter pilot

- status: remediation tickets and portfolio coverage can be resolved from canonical Postgres reports behind the frontend DTO contract.
- module: `src/stockanalysis/frontend/live_adapter.py`.
- source mode: `stockanalysis.frontend.api_adapter get --source fixture|live|auto`.
- verification: `scripts/verify_frontend_live_read_adapter.sh`.
- boundary: no production API server, no browser DB access, no write endpoint.

Phase 1.8: Runtime source mode

- status: local read-only HTTP runtime supports `--source fixture|live|auto`.
- default: `fixture`, preserving existing frontend smoke behavior.
- auto behavior: live-supported endpoints use DB only when `STOCKANALYSIS_PSQL_COMMAND` is configured; otherwise fixture fallback.
- verification: `scripts/verify_frontend_fixture_server.sh`.
- boundary: still local-only, no auth/RBAC, no write endpoint.

Phase 1.9: API runtime boundary

- status: runtime policy documented as `docs/frontend-api-runtime-boundary.md`.
- module: `src/stockanalysis/frontend/runtime_policy.py`.
- behavior: local unauthenticated runtime is loopback-only; production profile requires read-token auth, explicit CORS origin, and DB configuration for `live`/`auto`.
- verification: `scripts/verify_frontend_api_runtime_boundary.sh`.
- boundary: read-token is a deployment safety seam, not full user/role RBAC.

Phase 1.10: FastAPI read-only API server

- status: production-candidate read-only API server documented as `docs/frontend-api-server.md`.
- module: `src/stockanalysis/frontend/api_server.py`.
- DB boundary: `src/stockanalysis/frontend/db_pool.py` uses psycopg pool with `STOCKANALYSIS_DATABASE_URL`.
- behavior: `/__health` is public; `/__endpoints` and `/api/{path:path}` are protected in read-token mode.
- verification: `scripts/verify_frontend_api_server.sh`.

Phase 2: frontend scaffold

- status: fixture-only scaffold documented as `docs/apps-web-scaffold.md`.
- app: `apps/web`.
- routes: `/`, `/remediation`, `/data-health`, `/cycles`, `/events`, `/themes/ANNUAL_REPORTING`, `/recommendations/AAPL-2024-11-01`, `/theses/AAPL-bootstrap-v1`, `/portfolio/coverage`, `/performance`, `/ai-evidence/sec-event-aapl-10k-20240928`, `/source-documents/aapl-2024-10k-20240928`.
- verification: `scripts/verify_apps_web_scaffold.sh`.

Phase 3: daily cockpit and remediation UI

- implement `/`, `/remediation`, `/data-health`.
- add read-only ticket views first.
- add audited status update only after API contract is stable.

Phase 4: research explorer

- status: initial AI evidence/source document drilldown exists for one SEC fixture pair, and `/events` plus `/themes/ANNUAL_REPORTING` now connect event, theme, cycle, instrument, recommendation, thesis, and source document evidence.
- next expand filtering, pagination, and additional theme detail fixtures after live read adapter shape is stable.
- link event evidence, classifications, instrument impacts, source documents, and cycle snapshots.

Phase 5: thesis and performance review

- status: `/recommendations`, `/theses`, `/portfolio/coverage`, and `/performance` fixture-backed routes exist for one bootstrap portfolio/recommendation path.
- show score components, invalidation conditions, outcome labels, attribution lenses, and coverage exclusions.

Phase 6: operational hardening

- status: local browser visual QA exists for the expanded fixture-backed frontend.
- next: auth, RBAC, audit logs, alert destination, deployment, accessibility checks.

## Next Task

FastAPI read-only API server now exists and API operations have basic request id, timeout, structured log, liveness, readiness, deployment boundary hardening, and pagination conventions.

Implemented in `frontend-api-server-observability-hardening`:

- request id and structured logs.
- timeout and cancellation policy.
- readiness and liveness probes.

Implemented in `frontend-api-server-deployment-boundary`:

- deployment boundary documentation.
- runtime env template.
- reverse proxy/TLS assumptions.

Implemented in `frontend-api-pagination-conventions`:

- pagination conventions for list endpoints.

The next task should add:

- external metrics/log sink decision.
- keep write endpoints disabled until full auth/RBAC and audit trail exist.
