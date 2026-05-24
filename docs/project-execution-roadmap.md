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
- frontend contract/runtime: 17개 DTO contract, fixture server, initial live read adapter completeness, `--source fixture|live|auto`, runtime boundary policy, actual DB-backed HTTP live smoke, FastAPI read-only API server with psycopg pool, request id/timeout/structured log/readiness hardening, deployment boundary/env preflight, pagination conventions, SQL-level bounded pagination optimization, optional OTLP exporter local receiver smoke, secret-free alert rule reference, Next.js read-only cockpit routes including stock list/detail price chart pages, recommendation index/detail, read-only paper trading preview, and trading readiness cockpit.
- trading safety boundary: broker boundary, account permission, order limit policy, kill switch, paper validation, and order intent audit schema plus deterministic safety evaluator, read-only readiness DTO/page, broker-free paper validation audit writer workflow, and simulated paper safety bootstrap config.
- data operations foundation: daily/weekly/monthly cadence registry, read-only cadence CLI report, `/api/data-health` expected job health handoff, generic stdout/stderr/metadata artifact runner, repo-outside runtime env readiness gate, disposable/local runtime smoke, generic scheduler activation boundary wrapper, launchd install dry-run renderer, secret-free scheduler alert rule reference, manual exact-command approval packet, external manual activation preflight, first `stockanalysis-operations` backend orchestration CLI boundary.
- harness: task contract/plan/handoff/review directories and verification scripts.

## Not Done

아래는 아직 끝나지 않았다.

- actual managed deployment install, reverse proxy config, Alertmanager receiver routing, keyset cursor v2 if deep-page query plans require it.
- full auth/RBAC, actor identity, audit-enforced write APIs.
- actual recurring production data jobs with real credentials, runtime smoke, scheduler activation, and alerting.
- full migration of remaining non-verify data operations wrappers into the `stockanalysis-operations` backend boundary.
- broad AI provider gateway, model routing, vector/RAG runtime, eval pipeline.
- recommendation quality evaluation beyond deterministic bootstrap fixtures, the first read-only paper trading quality gate, and audit-only paper validation writer.
- real brokerage/order integration. Safety schema/evaluator/readiness screen, paper validation audit writer, and simulated paper safety config exist, but actual broker adapter, account credential setup, write API, execution reports, fills, kill-switch unlock, and live order submission remain out of scope until separately approved.

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
- Add default-disabled optional OTLP exporter pilot. Implemented in `frontend-api-otel-exporter-pilot`.
- Move live list reads from response-boundary slicing to SQL-level bounded windows. Implemented in `frontend-api-sql-pagination-optimization`.
- Add local OTLP receiver smoke for optional exporter egress. Implemented in `frontend-api-local-collector-smoke`.
- Add secret-free Prometheus-compatible alert rule reference. Implemented in `frontend-api-alert-rules`.

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

Implemented first slice:

- Define daily/weekly/monthly data operations cadence registry and data-health expected job handoff. Implemented in `data-operations-cadence-foundation`.
- Add generic repo-local stdout/stderr/metadata artifact runner for known cadence jobs. Implemented in `data-operations-artifact-runner`.
- Add repo-outside runtime env readiness gate for database, FRED, Alpha Vantage, SEC identity, portfolio snapshot source, LLM provider, market price history dependency, and artifact root. Implemented in `data-operations-runtime-env-readiness`.
- Add scheduler-free disposable/local runtime smoke for representative `macro-weekly` fixture job through the artifact runner. Implemented in `data-operations-runtime-smoke`.
- Add generic scheduler activation boundary wrapper with env readiness preflight, command redaction, skip-date artifact, and artifact runner invocation. Implemented in `data-operations-scheduler-activation-boundary`.
- Add launchd scheduler install dry-run renderer for daily/weekly cadence jobs, repo-outside output, and no host install path writes. Implemented in `data-operations-scheduler-install-dry-run`.
- Add secret-free scheduler alert rule reference for missing, failed, stale, timeout, artifact missing, and preflight failure states. Implemented in `data-operations-scheduler-alert-boundary`.
- Add manual activation runbook with approval gate, rollback, disable, and evidence checklist before host scheduler activation. Implemented in `data-operations-scheduler-activation-runbook`.
- Add operator dry-run evidence bundle that rehearses readiness, scheduler preflight, install rendering, and alert validation without host scheduler mutation. Implemented in `data-operations-scheduler-operator-dry-run`.
- Add machine-readable activation approval gate that blocks scheduler activation unless repo-outside dry-run evidence and explicit approval record are valid. Implemented in `data-operations-scheduler-activation-approval-gate`.
- Add live activation request packet that turns approved evidence into `pending_explicit_user_approval` without host scheduler mutation. Implemented in `data-operations-live-scheduler-activation-request`.
- Add user decision gate that validates approve/deny decision records without host scheduler mutation. Implemented in `data-operations-live-scheduler-activation-user-decision`.
- Add final preflight that revalidates approved activation evidence and fresh runtime readiness without host scheduler mutation. Implemented in `data-operations-live-scheduler-activation-final-preflight`.
- Add host activation plan that turns passed final preflight into reviewable command and rollback previews without host scheduler mutation. Implemented in `data-operations-live-scheduler-host-activation-plan`.
- Add host activation execution request that asks for explicit execution approval from a reviewed host activation plan without host scheduler mutation. Implemented in `data-operations-live-scheduler-host-activation-execution-request`.
- Add host activation execution decision gate that validates approve/deny execution records without host scheduler mutation. Implemented in `data-operations-live-scheduler-host-activation-execution-decision`.
- Add backend orchestration boundary that introduces `stockanalysis-operations`, shared repo-outside path/report IO policy, and converts the representative host activation execution decision wrapper to a thin CLI wrapper. Implemented in `data-operations-backend-orchestration-boundary`.
- Add host activation execution final preflight that revalidates approved execution decision, reviewed host plan, command preview consistency, and fresh runtime readiness without host scheduler mutation. Implemented in `data-operations-live-scheduler-host-activation-execution-final-preflight`.
- Add host activation execution gate that validates final preflight and optional explicit host mutation confirmation, but still does not execute `launchctl` or write host LaunchAgents inside Codex. Implemented in `data-operations-live-scheduler-host-activation-execution`.
- Add manual host scheduler activation exact-command approval packet that validates approve/abort records and command drift, but still does not execute `launchctl` or write host LaunchAgents inside Codex. Implemented in `manual-host-scheduler-activation-explicit-approval`.
- Add external manual host scheduler activation preflight that checks exact-command approval plus fresh runtime env readiness, but still does not execute `launchctl` or write host LaunchAgents inside Codex. Implemented in `manual-host-scheduler-activation-preflight`.
- Add local live MVP runtime bootstrap that prepares a Python 3.13 venv, repo-outside local env, FastAPI/Next smoke path, and fixes the scheduler exact-command `$HOME` path blocker before any physical scheduler activation. Implemented in `local-live-mvp-runtime`.
- Add no-cost Alpha Vantage market price operation guardrails: free daily endpoint fallback, per-run throttling/budget skip, repo-outside watchlist plus cross-run daily provider budget ledger, and read-only API/frontend provider budget visibility. Implemented in `free-market-backfill-throttle`, `free-market-backfill-budget-ledger`, and `free-market-budget-frontend-visibility`.
- Reframe recurring automation target from Mac LaunchAgents to a server-side scheduler + `stockanalysis-operations` worker architecture. Mac launchd remains local MVP/operator-only, not the final service scheduler. Implemented in `server-side-scheduler-architecture`.
- Correct the immediate direction back to local-first runtime: external server scheduler selection is a future option, while current work should make local Postgres, local operations worker, FastAPI, and Next cockpit reliable first. Implemented in `local-first-runtime-direction`.
- Add a secret-free read-only local runtime status command that reports local env files, DB/artifact boundaries, FastAPI/Next probes, manual worker commands, and why LaunchAgents remain blocked. Implemented in `local-runtime-status-orchestrator`.
- Add a preview-first manual local ingest smoke command for market/news/AI jobs that only writes data with explicit `--execute` and records artifact-run metadata. Implemented in `manual-local-ingest-smoke`.
- Add read-only `/api/data-health` and `/data-health` visibility for the latest repo-outside manual local ingest smoke summary. Implemented in `manual-local-ingest-data-health-visibility`.
- Align the free local news-cluster AI evidence runner with the `event-intelligence-weekly` data-health cadence run history. Implemented in `local-ai-pipeline-run-alignment`.
- Add a bounded local process worker that reuses the proven manual local ingest smoke cycle for market/news/AI jobs without Mac LaunchAgents or external scheduler deployment. Implemented in `local-ingest-worker-loop`.
- Add read-only `/api/data-health` and `/data-health` visibility for the latest repo-outside local ingest worker run summary. Implemented in `local-ingest-worker-data-health-visibility`.
- Add a secret-free server-side scheduler invocation packet for cron/systemd/Kubernetes/managed scheduler candidates to call `stockanalysis-operations local-ingest-worker-run` without deploying a scheduler or mutating host state. Implemented in `server-scheduler-invocation-boundary`.
- Add a zero-budget server scheduler deployment target decision gate that marks external scheduler deployment blocked while DB/runtime remain local-only, and recommends GitHub Actions only after hosted DB/runtime exists. Implemented in `server-scheduler-deployment-target-decision`.
- Add a hosted DB/runtime decision gate that recommends Supabase Free Postgres + GitHub Actions worker setup as the zero-budget path, while keeping provisioning, secrets, migrations, and scheduler deployment out of scope. Implemented in `hosted-database-runtime-decision`.
- Add an operating-data orchestrator that replaces manual EC2 repair command sequences with a preview-first backend runner for missing price symbols, macro refresh, signal/recommendation/thesis chain, portfolio snapshot/review, performance outcome schedule, and broker-free paper validation audit. Implemented in `operating-data-orchestrator`.
- Split that runner into schedule-appropriate operating profiles so news/AI can run intraday, market candles daily, recommendations/holding review daily, macro weekly, performance monthly, and full recovery only manually. Implemented in `operating-data-profile-scheduler`.
- Activate the EC2 `systemd` profile scheduler for `news-intraday`, `market-daily`, `decision-daily`, `macro-weekly`, and `performance-monthly`, and expose the installed scheduler status through `/api/data-health`. Implemented in `ec2-systemd-profile-scheduler`.

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

Current task group: `quality-and-evaluation-hardening`.

The project is no longer in the Supabase setup or Mac local-first decision stage. Current runtime reality is EC2-hosted FastAPI read-only backend, Next.js cockpit, Postgres canonical DB, and profile-based `systemd` scheduler. The implemented product path is now:

| Area | Current State | Not Done |
| --- | --- | --- |
| Runtime | EC2 FastAPI/Next.js/systemd profile scheduler is the active operating candidate. | Production hardening, auth/RBAC, observability sink, deployment manifest maturity. |
| Data | RSS news, Korean translation, market price, macro, SEC, event enrichment, hierarchical propagation, cycle snapshot, recommendation, paper validation, quality audit, and eval dataset runners are connected through backend CLI runners. | Provider quota resilience and longer-lived outcome history. |
| AI | Codex OAuth batch is used for translation/news extraction; deterministic fallback remains available; AI artifacts and invocations are logged. News eval scoring and cycle community AI summary v2 runners exist. | EC2 Codex OAuth token is currently invalidated for the new community summary smoke; EC2/AWS access is currently blocked by SSH timeout and AWS account-closed sign-in state. |
| Cycle Graph | Postgres ontology-lite, multi-hop impact propagation, cycle hierarchy snapshot, cycle map frontend, and recommendation quality calibration runner are implemented. | More outcome samples are needed before any component weight change. |
| Frontend | Core pages exist and read live backend DTOs. Home/data-health/intelligence/cycle-map/paper-trading now share a “what to review today” decision strip; AI evidence detail has a source-to-recommendation trace path. | EC2 visual smoke for the latest UX commits is pending until SSH/AWS access is restored. |
| Trading | Broker boundary, paper safety, paper validation audit, order intent audit tables, and clearer paper trading status UI exist. | Live broker submit remains excluded; EC2 visual smoke is pending until SSH/AWS access is restored. |

Completed in this task group:

- `project-roadmap-reality-sync`
- `cycle-ai-e2e-quality-audit`
- `news-ai-eval-dataset-and-scoring`
- `cycle-community-ai-summary-v2`: EC2 fixture/fallback smoke passed, but real Codex OAuth summary needs EC2 re-login because the token is invalidated.
- `recommendation-quality-calibration`: implemented and EC2 smoke passed with `run_id=705`, `eval_run_id=3`; outcome sample is still insufficient, so recommendation weights remain unchanged.
- `decision-cockpit-ux-v2`: implemented locally and pushed in `3fe42a7`; EC2 smoke pending because SSH/AWS access is blocked.
- `ai-evidence-review-visibility-v2`: implemented locally and pushed in `8aa3943`; EC2 smoke pending because SSH/AWS access is blocked.
- `paper-trading-status-clarity`: implemented locally and pushed in `6cb1c60`; EC2 smoke pending because SSH/AWS access is blocked.
- `recommendation-outcome-backfill`: implemented locally and pushed in `2d9c3bd`; EC2 smoke pending because SSH/AWS access is blocked.

Current remaining task:

1. `codex-oauth-ec2-relogin-smoke`: restore target AWS/EC2 access, deploy latest branch to EC2, refresh EC2 Codex OAuth login, rerun real Codex OAuth community summary smoke, and compare fallback vs LLM artifacts. Current blocker evidence is recorded in `docs/tasks/codex-oauth-ec2-relogin-smoke/handoff.md`.

Current guardrail: do not change scoring weights, benchmark splits, or live broker submit in this task group. If a task does not improve live data truth, AI evidence quality, recommendation evaluation, or user-facing clarity, it is lower priority.

## Focus Rules

- If a task does not improve live data truth, runtime safety, AI evidence quality, recommendation evaluation, or operator visibility, it is lower priority.
- If a task changes benchmark, schema, scoring, or auth boundary, it needs explicit task contract and verification.
- If frontend work is requested before live read completion, keep it limited to consuming existing DTOs unless explicitly approved.
- If AI work is requested before model gateway/eval exists, implement gateway/eval first rather than prompt-only features.
