# Verification Plan

이 문서는 프로젝트 차원에서 "무엇이 완료의 증거인가"를 고정하기 위한 문서다.

task마다 흔들리게 두지 않는 편이 좋다.

## Scope

- 대상 기능군 또는 시스템: AI 기반 중장기 투자 운영 시스템의 문서, 하네스, 이후 추가될 데이터 파이프라인, 사이클 엔진, thesis 엔진, 추천/검토 리포트

## Automated Checks

- 명령: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task foundation-architecture`
- 무엇을 증명하는가: repo-level 하네스 파일과 현재 task-level 문서가 최소 운영 가능 상태인지 검증한다.
- 통과 조건: exit code 0, missing file 또는 placeholder 관련 오류가 없다.

- 명령: `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`
- 무엇을 증명하는가: scaffold placeholder가 실제 프로젝트 내용으로 치환되었는지 확인한다.
- 통과 조건: 출력이 없다.

- 명령: `find docs -maxdepth 3 -type f | sort`
- 무엇을 증명하는가: repo/task 수준 핵심 문서가 기대 경로에 존재하는지 확인한다.
- 통과 조건: `docs/project-foundation.md`, `docs/agent-work-harness-evaluation.md`, `docs/verification-plan.md`, `docs/tasks/foundation-architecture/contract.md`, `docs/tasks/foundation-architecture/handoff.md`가 목록에 보인다.

- 명령: `bash scripts/verify_project_execution_roadmap.sh`
- 무엇을 증명하는가: 현재 진행상황, 미완료 영역, 고정 실행 순서, immediate next task가 repo-local roadmap과 하네스에 기록되어 있는지 확인한다.
- 통과 조건: `docs/project-execution-roadmap.md`, `docs/tasks/project-execution-roadmap/` 문서, AGENTS repo map, completed frontend API live/runtime/observability slices, completed `data-operations-cadence-foundation`, `data-operations-artifact-runner`, `data-operations-runtime-env-readiness`, `data-operations-runtime-smoke`, `data-operations-scheduler-activation-boundary`, `data-operations-scheduler-install-dry-run`, `data-operations-scheduler-alert-boundary`, `data-operations-scheduler-activation-runbook`, `data-operations-scheduler-operator-dry-run`, `data-operations-scheduler-activation-approval-gate`, `data-operations-live-scheduler-activation-request`, `data-operations-live-scheduler-activation-user-decision`, `data-operations-live-scheduler-activation-final-preflight`, `data-operations-live-scheduler-host-activation-plan`, `data-operations-live-scheduler-host-activation-execution-request`, `data-operations-live-scheduler-host-activation-execution-decision`, `data-operations-backend-orchestration-boundary`, `data-operations-live-scheduler-host-activation-execution-final-preflight`, `data-operations-live-scheduler-host-activation-execution`, `manual-host-scheduler-activation-explicit-approval`, `manual-host-scheduler-activation-preflight`, `local-live-mvp-runtime`, `manual-local-ingest-smoke`, `manual-local-ingest-data-health-visibility`, `local-ai-pipeline-run-alignment`, `local-ingest-worker-loop`, `local-ingest-worker-data-health-visibility`, `server-scheduler-invocation-boundary`, `server-scheduler-deployment-target-decision`, `hosted-database-runtime-decision`, immediate next task `supabase-free-postgres-setup-packet`, API runtime guardrail이 모두 확인된다.

- 명령: `bash scripts/verify_server_scheduler_invocation_boundary.sh`
- 무엇을 증명하는가: 외부 cron/systemd/Kubernetes/managed scheduler가 호출할 `stockanalysis-operations local-ingest-worker-run` invocation packet이 secret 없이 생성되고, 실제 scheduler 배포/host mutation 없이 검증되는지 확인한다.
- 통과 조건: compileall, focused unittest, CLI smoke, repo-outside env/output enforcement, no `launchctl`, no DB URL/API key/token leak, task docs가 모두 통과한다.

- 명령: `bash scripts/verify_server_scheduler_deployment_target_decision.sh`
- 무엇을 증명하는가: 무료 조건과 현재 local-only DB/runtime 제약에서 외부 scheduler 배포가 가능한지, GitHub Actions/systemd/Kubernetes/managed/local 후보 중 무엇이 추천/차단되는지 secret 없이 판정하는지 확인한다.
- 통과 조건: compileall, focused unittest, CLI smoke, local-only state blocked, hosted DB state GitHub Actions candidate, existing host state systemd candidate, no scheduler artifact/no secret leak가 모두 통과한다.

- 명령: `bash scripts/verify_hosted_database_runtime_decision.sh`
- 무엇을 증명하는가: 무료 hosted DB/runtime 경로가 Supabase Free Postgres + GitHub Actions worker setup으로 정리되고, 실제 DB 생성/secret 작성/workflow 생성 없이 다음 setup packet으로 넘어가는지 확인한다.
- 통과 조건: compileall, focused unittest, CLI smoke, default setup-required decision, hosted DB ready state, existing host ready state, local-only explicit state, no DB URL/API key/token leak가 모두 통과한다.

- 명령: `bash scripts/verify_operating_data_orchestrator.sh`
- 무엇을 증명하는가: 실제 화면에 필요한 운영 데이터 순서가 수동 EC2 보정이 아니라 `stockanalysis-operations operating-data-run` backend boundary로 preview/execute 가능하고, 자동 운영 profile이 뉴스/AI intraday, market daily, decision daily, macro weekly, performance monthly, full recovery로 분리되는지 확인한다.
- 통과 조건: operating-data orchestrator/artifact runner/CLI/cadence/live adapter focused unittest, profile preview CLI smoke, repo-outside env/output enforcement, no DB URL/API key/token leak, task docs가 모두 통과한다.

- 명령: `bash scripts/verify_frontend_architecture.sh`
- 무엇을 증명하는가: investment cockpit 방향, route map, API boundary, AI boundary, security boundary, phased implementation, fixture-only `apps/web` scaffold가 문서와 파일로 정렬되어 있는지 확인한다.
- 통과 조건: `docs/frontend-architecture.md`와 task docs가 존재하고, frontend doc에 cockpit, route map, data boundary, AI boundary, security boundary, implementation phases가 포함되며, `apps/web` scaffold가 존재하고 root-level `app` scaffold는 없는 것이 확인된다.

- 명령: `bash scripts/verify_frontend_api_contract.sh`
- 무엇을 증명하는가: daily cockpit, remediation tickets, data health, stock list/detail, paper trading preview, trading readiness, cycle state, recommendation detail, thesis detail, portfolio coverage, performance outcomes, AI evidence, source document, event list, theme detail read DTO contract와 example JSON이 고정되었는지 확인한다.
- 통과 조건: `docs/frontend-api-contract.md`, `docs/api/frontend/contract-index.json`, sixteen example JSON이 존재하고, contract version과 endpoint/example mapping, common response shape, 핵심 field assertions가 모두 통과하며, root-level `app` scaffold가 없는 것이 확인된다.

- 명령: `bash scripts/verify_frontend_api_adapter.sh`
- 무엇을 증명하는가: frontend API contract examples를 반환하는 read-only Python adapter와 CLI가 동작하는지 확인한다.
- 통과 조건: `compileall`, adapter unit tests, frontend API contract verification, CLI `list`, CLI `get --path /api/dashboard/today`, unknown path stable error, root-level `app` scaffold 부재 확인이 모두 통과한다.

- 명령: `bash scripts/verify_frontend_live_read_adapter.sh`
- 무엇을 증명하는가: frontend API adapter가 fixture contract를 유지하면서 일부 endpoint를 canonical Postgres read report 기반 live DTO로 변환할 수 있는지 확인한다.
- 통과 조건: `compileall`, live adapter unit tests, adapter regression tests, frontend API adapter verification, `--source auto` fixture fallback, `--source live` missing-config stable error, root-level `app` scaffold 부재 확인이 모두 통과한다.

- 명령: `bash scripts/verify_frontend_fixture_server.sh`
- 무엇을 증명하는가: frontend API fixture adapter가 local read-only HTTP server로 노출되고 browser fetch 준비가 되었는지 확인한다.
- 통과 조건: `compileall`, fixture server unit tests, frontend API adapter verification, CLI help smoke, in-process HTTP runtime smoke, known path response, query-string path response, `--source auto` fixture fallback, `--source live` missing-config 503, unknown path 404, write method 405, root-level `app` scaffold 부재 확인이 모두 통과한다.

- 명령: `bash scripts/verify_frontend_api_runtime_boundary.sh`
- 무엇을 증명하는가: frontend read-only HTTP runtime이 local/production profile, CORS, read-token auth seam, startup guard를 적용하는지 확인한다.
- 통과 조건: `compileall`, fixture server regression, local non-loopback unauthenticated startup rejection, read-token protected API paths, public health, production profile startup guard, guarded production metadata smoke가 모두 통과한다.

- 명령: `bash scripts/verify_frontend_runtime_db_smoke.sh`
- 무엇을 증명하는가: frontend read-only HTTP runtime이 fixture JSON이 아니라 disposable Postgres에 적재된 canonical state를 `source=live`로 읽어 production-profile HTTP DTO를 반환하는지 확인한다.
- 통과 조건: Docker Postgres migration/seed/pipeline bootstrap, production-profile live runtime startup, public health, unauthorized read rejection, authorized dashboard/data-health/cycle/event/theme/ticket/recommendation/thesis/performance/source-document HTTP reads가 모두 통과한다.

- 명령: `bash scripts/verify_frontend_api_server.sh`
- 무엇을 증명하는가: FastAPI read-only frontend API server가 psycopg pool로 disposable Postgres state를 읽고 request id/probe/runtime boundary와 Next.js server-side token forwarding cockpit route smoke까지 통과하는지 확인한다.
- 통과 조건: FastAPI/db pool unit tests, Docker Postgres migration/seed/pipeline bootstrap, Uvicorn production-profile startup, public live/health/ready probes, request id propagation, unauthorized read rejection, authorized live DTO reads, Next typecheck/build/home route smoke가 모두 통과한다.

- 명령: `bash scripts/verify_frontend_api_server_deployment_boundary.sh`
- 무엇을 증명하는가: FastAPI read-only frontend API server의 repo-outside runtime env template, env preflight, run wrapper, secret redaction, loopback-behind-TLS deployment boundary가 동작하는지 확인한다.
- 통과 조건: renderer/checker/wrapper syntax, repo 내부 env output/file 거부, unedited template failure, valid temp env readiness success, wrapper `--preflight-only`, DB URL/read token redaction이 모두 통과한다.

- 명령: `bash scripts/verify_frontend_api_pagination_conventions.sh`
- 무엇을 증명하는가: frontend list endpoint의 `limit`, opaque `cursor`, `next_cursor`, invalid pagination error, DTO examples, TypeScript response type이 같은 contract를 따르는지 확인한다.
- 통과 조건: pagination helper/API adapter/live adapter/FastAPI tests, CLI pagination smoke, collection examples top-level pagination metadata, TypeScript optional pagination type이 모두 통과한다.

- 명령: `bash scripts/verify_frontend_api_observability_sink_decision.sh`
- 무엇을 증명하는가: FastAPI read-only frontend API server의 외부 telemetry egress boundary가 OpenTelemetry Collector 중심으로 문서화되고, Loki/Prometheus/Alertmanager reference stack, high-cardinality guardrail, 다음 OTLP exporter pilot task가 고정되어 있는지 확인한다.
- 통과 조건: decision doc, task docs, implementation plan, roadmap, README, AGENTS, verification script reference가 모두 존재하고 핵심 결정 문구가 검색된다.

- 명령: `bash scripts/verify_frontend_api_otel_exporter_pilot.sh`
- 무엇을 증명하는가: FastAPI read-only frontend API server가 기본 disabled mode에서는 OpenTelemetry package 없이 동작하고, opt-in OTLP mode는 safe endpoint validation, optional dependency boundary, bounded access telemetry field를 제공하는지 확인한다.
- 통과 조건: observability/API server py_compile, targeted unittest, optional dependency extra, env constants, docs, roadmap, AGENTS next task, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_frontend_api_sql_pagination_optimization.sh`
- 무엇을 증명하는가: frontend live list endpoint가 기존 pagination contract를 유지하면서 SQL/report boundary에 `limit + 1`과 cursor offset을 전달하고, summary는 full filtered set 기준으로 유지하는지 확인한다.
- 통과 조건: pagination/live adapter/remediation/coverage py_compile, targeted unittest, cycle/event/performance/remediation/coverage bounded SQL markers, docs, roadmap, AGENTS next task, verification script reference가 모두 통과한다.

- 명령: `PYTHON_BIN=<python-with-stockanalysis-otel-extra> bash scripts/verify_frontend_api_local_collector_smoke.sh`
- 무엇을 증명하는가: FastAPI read-only frontend API server의 optional OTLP exporter가 local OTLP/HTTP receiver로 실제 trace payload를 전송하고, public metadata가 endpoint를 노출하지 않는지 확인한다.
- 통과 조건: smoke helper/API server py_compile, observability/API server targeted unittest, local OTLP receiver smoke에서 `/v1/traces` POST 수신, docs, roadmap, AGENTS next task, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_frontend_api_alert_rules.sh`
- 무엇을 증명하는가: FastAPI read-only frontend API server의 첫 Prometheus-compatible alert rule reference가 secret/receiver 없이 down/not-ready/5xx/timeout/latency/adapter-error 조건을 고정하는지 확인한다.
- 통과 조건: alert rule YAML, stdlib validator, six alert names, bounded metric labels, docs, roadmap, AGENTS next task, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_ai_retrieval_adapter_foundation.sh`
- 무엇을 증명하는가: RAG/ontology 도입 전 단계로 external vector DB, graph DB, live LLM 호출 없이 내부 retrieval adapter, Postgres evidence neighborhood SQL, ontology-lite validation SQL 경계가 존재하는지 확인한다.
- 통과 조건: AI retrieval modules py_compile, retrieval/evidence graph/ontology validation targeted unittest, read-only SQL marker, task docs, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_ai_retrieval_neighborhood_api.sh`
- 무엇을 증명하는가: AI evidence neighborhood foundation이 read-only frontend API DTO와 종목 상세 화면에 연결되고, vector storage URI/secret 없이 Postgres canonical graph 관계를 노출하는지 확인한다.
- 통과 조건: evidence graph/live adapter py_compile, targeted live adapter tests, stock detail reader/type/page markers, task docs, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_news_rss_local_chunk_index.sh`
- 무엇을 증명하는가: RSS source document가 external embedding API/live LLM 없이 local deterministic `ai.document_chunk`와 `ai.embedding_index` metadata로 연결되어 AI 증거 관계망의 RAG 준비 상태가 채워지는지 확인한다.
- 통과 조건: chunk index runner/CLI py_compile, targeted unittest, local-only/no-cost SQL marker, task docs, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_news_rss_raw_body_fetch.sh`
- 무엇을 증명하는가: RSS source document가 무료 공개 기사 URL의 raw HTML artifact와 연결되고, fetch URL 안전장치/byte limit/pipeline run evidence가 secret 없이 유지되는지 확인한다.
- 통과 조건: raw fetch runner/CLI py_compile, targeted unittest, public URL guardrail, bounded body marker, no paid API/live LLM marker, task docs, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_news_rss_raw_body_chunk_index.sh`
- 무엇을 증명하는가: 저장된 RSS raw HTML artifact가 `artifact_root` 경계 안에서만 읽혀 본문 텍스트 chunk와 local embedding metadata로 연결되는지 확인한다.
- 통과 조건: raw body chunk runner/CLI py_compile, targeted unittest, HTML extraction, artifact-root guardrail, local/no-cost chunk and embedding SQL marker, task docs, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_ai_news_cluster_map.sh`
- 무엇을 증명하는가: 저장된 RSS `news_cluster_summary` AI artifact가 read-only API와 `/intelligence` 화면에 노출되고, 원천 문서 chunk/embedding readiness를 vector URI/secret 없이 보여주는지 확인한다.
- 통과 조건: live adapter/pagination py_compile, targeted live adapter tests, news cluster SQL markers, frontend type/client/page markers, task docs, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_cadence_foundation.sh`
- 무엇을 증명하는가: Data Operations Loop의 daily/weekly/monthly cadence registry, read-only CLI report, `/api/data-health` expected job missing/stale/failed handoff가 secret 없이 고정되는지 확인한다.

- 명령: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_safety`
- 무엇을 증명하는가: broker boundary, 계좌 권한, 주문 한도, kill switch, paper validation, human approval, audit-only order intent SQL이 실제 주문 제출 없이 deterministic safety gate로 동작하는지 확인한다.
- 통과 조건: default blocked, configured paper approval, configured live approval, remaining paper conflicts block live, oversized order block, audit SQL secret-free assertions가 모두 통과한다.
- 통과 조건: cadence registry py_compile, targeted unittest, CLI JSON smoke, data-health SQL marker, docs, roadmap, AGENTS next task, verification script reference가 모두 통과한다.

- 명령: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_frontend_live_adapter tests.test_frontend_api_adapter tests.test_trading_safety`
- 무엇을 증명하는가: trading readiness DTO가 canonical `trading.*` safety tables를 read-only로 읽고, broker secret 값 없이 broker boundary/account permission/order limit/kill switch/paper validation/audit summary를 노출하는지 확인한다.
- 통과 조건: `/api/trading/readiness` fixture/live contract shape, read-only SQL markers, secret redaction, existing paper trading and safety evaluator regressions가 모두 통과한다.

- 명령: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_paper_validation tests.test_data_operations_cli tests.test_trading_safety`
- 무엇을 증명하는가: `/api/paper-trading/preview` 결과가 broker-free deterministic safety evaluator를 거쳐 `trading.paper_validation_run`과 `trading.order_intent_audit` write SQL/CLI report로 변환되는지 확인한다.
- 통과 조건: SQL에 paper validation/audit table이 포함되고 `submitted_to_broker=true`가 없으며, safety config lookup/report가 broker secret을 노출하지 않고, `stockanalysis-operations paper-validation-audit-run` CLI가 repo-outside env policy와 runtime args를 지킨다.

- 명령: `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_trading_paper_safety_bootstrap tests.test_data_operations_cli tests.test_trading_paper_validation tests.test_trading_safety`
- 무엇을 증명하는가: simulated paper broker/account/order-limit 설정이 실제 브로커 없이 `trading.broker_boundary`, `trading.account_permission`, `trading.order_limit_policy`로 upsert 가능하고 operations CLI에서 재현 가능한지 확인한다.
- 통과 조건: SQL이 paper-only safety rows를 upsert하고 `supports_order_submit=false`, `submitted_to_broker_count=0`, `secret_configured=false`, kill switch unchanged를 유지하며, repo-outside env policy와 CLI runtime args가 테스트로 고정된다.

- 명령: `bash scripts/verify_data_operations_artifact_runner.sh`
- 무엇을 증명하는가: known data operations cadence job을 repo-local wrapper로 실행하면 stdout/stderr/metadata artifact가 저장되고 command argv secret redaction과 child exit-code propagation이 동작하는지 확인한다.
- 통과 조건: artifact runner py_compile, runner/CLI targeted unittest, temp artifact root CLI smoke, metadata/stdout/stderr file assertions, docs, roadmap, AGENTS next task, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_runtime_env_readiness.sh`
- 무엇을 증명하는가: data operations scheduler 활성화 전에 trusted repo-outside env file이 database, FRED, Alpha Vantage, SEC identity, portfolio snapshot source, LLM provider, market price history dependency, artifact root readiness를 secret-free JSON으로 통과/실패 판정하는지 확인한다.
- 통과 조건: env readiness py_compile, unit/CLI tests, repo-inside template output refusal, unedited template failure, valid temp env readiness success, secret value non-leakage, repo-inside env file refusal, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_runtime_smoke.sh`
- 무엇을 증명하는가: env readiness를 통과한 trusted repo-outside env로 representative `macro-weekly` job을 artifact runner에 태워 disposable Postgres에 fixture macro batch를 실행하고 stdout/stderr/metadata artifact를 남기는지 확인한다.
- 통과 조건: runtime smoke py_compile, unit tests, repo-inside env refusal, Docker Postgres migration/seed, fixture macro batch via `smoke_data_operations_runtime.sh`, stdout/stderr/metadata/stdout JSON artifacts, macro row counts, `ops.pipeline_run` success rows, secret non-leakage, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_scheduler_activation_boundary.sh`
- 무엇을 증명하는가: actual scheduler 설치 전에 generic scheduler wrapper가 env readiness, known cadence job preflight, command redaction, configured skip-date artifact, non-skip artifact runner invocation을 수행하고 host scheduler artifacts를 만들지 않는지 확인한다.
- 통과 조건: scheduler boundary py_compile, targeted unit tests, missing command refusal, repo-inside env refusal, preflight redaction, skip artifact creation, non-skip `data-operations-run` artifact metadata, no `.github/workflows`/`cron`/`launchd` activation artifacts, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_scheduler_install_dry_run.sh`
- 무엇을 증명하는가: generic data operations scheduler wrapper를 호출하는 launchd plist와 manifest가 repo-outside dry-run output에 렌더링되고, env/output repo-inside path, sensitive command argv, monthly first-business-day jobs, host scheduler path writes가 거부되는지 확인한다.
- 통과 조건: scheduler install py_compile, targeted unit tests, repo-inside env/output refusal, sensitive command refusal, monthly job rejection, rendered plist/manifest contents, no secret leakage, no host LaunchAgents path writes, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_scheduler_alert_boundary.sh`
- 무엇을 증명하는가: Data Operations scheduler health alert rule reference가 missing/failed/stale/timeout/artifact/preflight states를 secret-free Prometheus-compatible rules로 고정하고, receiver/secret/dynamic business labels를 포함하지 않는지 확인한다.
- 통과 조건: alert rule validator py_compile, expected six alert names, expected metric names, bounded selector labels, no receiver/webhook/secret tokens, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_scheduler_activation_runbook.sh`
- 무엇을 증명하는가: actual host scheduler activation 전에 manual approval, preflight, install dry-run, rollback, disable, evidence checklist가 문서화되고 검증되며, repo-local scripts가 host launchd state를 변경하지 않는지 확인한다.
- 통과 조건: runbook docs/task files, preflight/install-dry-run/alert validation markers, `launchctl` reference-only activation/rollback/disable markers, no data operations runtime/render script host scheduler mutation, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_scheduler_operator_dry_run.sh`
- 무엇을 증명하는가: activation runbook을 실제 host scheduler mutation 없이 repo-outside temporary paths에서 readiness, scheduler preflight, install dry-run, alert validation, evidence bundle 생성까지 리허설하는지 확인한다.
- 통과 조건: operator dry-run py_compile, unit tests, temp env/output/artifact root, evidence files, secret non-leakage, repo-inside env/output refusal, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_scheduler_activation_approval_gate.sh`
- 무엇을 증명하는가: operator dry-run evidence가 있어도 명시 approval record 없이는 scheduler activation이 blocked로 남고, approval record가 있어도 code path가 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: approval gate py_compile, unit tests, pending/approved gate reports, secret non-leakage, repo-inside evidence/approval refusal, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_live_scheduler_activation_request.sh`
- 무엇을 증명하는가: 승인된 activation gate와 operator dry-run evidence가 있어도 live scheduler activation은 `pending_explicit_user_approval` 요청 패킷으로만 남고, code path가 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: activation request py_compile, unit tests, approved request report, pending gate rejection, secret non-leakage, repo-inside evidence refusal, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_live_scheduler_activation_user_decision.sh`
- 무엇을 증명하는가: activation request packet에 대해 approve/deny decision record를 검증하되, approve도 이 task 안에서는 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: activation decision py_compile, unit tests, missing/approve/deny decision reports, secret non-leakage, repo-inside request/decision refusal, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_live_scheduler_activation_final_preflight.sh`
- 무엇을 증명하는가: approve decision 이후에도 fresh runtime env readiness와 request/approval/dry-run evidence chain을 다시 검증하고, 통과해도 host activation plan으로만 이동하며 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: final preflight py_compile, unit tests, approve/deny/runtime-readiness reports, secret non-leakage, repo-inside decision/env/output refusal, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_live_scheduler_host_activation_plan.sh`
- 무엇을 증명하는가: passed final preflight와 activation request evidence를 operator review용 JSON/Markdown host activation plan으로 변환하되 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: host activation plan py_compile, unit tests, repo-outside evidence chain, JSON/Markdown plan output, command/rollback preview, secret non-leakage, denied preflight/repo-inside path refusal, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_request.sh`
- 무엇을 증명하는가: reviewed host activation plan을 explicit execution approval request packet으로 변환하되 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: execution request py_compile, unit tests, repo-outside evidence chain, pending execution approval request output, command/rollback preview, secret non-leakage, malformed plan/repo-inside path refusal, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_decision.sh`
- 무엇을 증명하는가: pending execution approval request에 대한 approve/deny decision record를 검증하되 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: execution decision py_compile, operations CLI/path/report IO py_compile, unit tests, repo-outside evidence chain, missing/approve/deny decision reports, secret non-leakage, mismatched request/repo-inside path refusal, thin wrapper delegation to `stockanalysis.operations.cli`, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli -v`
- 무엇을 증명하는가: `stockanalysis-operations` backend CLI boundary가 cadence report와 host activation execution decision report를 shell-owned orchestration 없이 처리하고, repo-inside input/output policy를 Python에서 강제하는지 확인한다.
- 통과 조건: CLI cadence JSON, repo-outside output write, repo-inside execution request refusal, path policy tests가 모두 통과한다.

- 명령: `bash scripts/verify_manual_local_ingest_data_health_visibility.sh`
- 무엇을 증명하는가: market/news/AI 수동 ingest smoke summary가 repo 밖 파일로 저장되고 `/api/data-health`/`/data-health`가 secret 없이 읽을 수 있는 read model을 제공하는지 확인한다.
- 통과 조건: `manual-local-ingest-smoke --output` summary 생성, sanitized visibility reader, focused live adapter tests, secret non-leakage가 모두 통과한다.

- 명령: `bash scripts/verify_local_ai_pipeline_run_alignment.sh`
- 무엇을 증명하는가: 무료 로컬 뉴스 클러스터 evidence runner가 direct call 기본값은 유지하면서 operations CLI에서는 `/api/data-health`가 기대하는 `event_intelligence_llm_extract` run history로 기록되는지 확인한다.
- 통과 조건: runner/CLI py_compile, focused unit tests, explicit pipeline name override smoke, docs, roadmap, AGENTS current task, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_local_ingest_worker_loop.sh`
- 무엇을 증명하는가: 검증된 market/news/AI manual local ingest smoke를 Mac LaunchAgents 없이 bounded local process worker로 실행하고, repo-outside latest smoke summary를 갱신할 수 있는지 확인한다.
- 통과 조건: local worker/CLI py_compile, focused unit tests, no-write preview CLI smoke, repo-outside worker/smoke reports, docs, roadmap, AGENTS current task, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_local_ingest_worker_data_health_visibility.sh`
- 무엇을 증명하는가: local ingest worker report가 repo 밖 파일에서 secret-free read model로 로드되고 `/api/data-health`와 `/data-health`가 worker 상태를 manual smoke 및 scheduler activation과 분리해서 보여주는지 확인한다.
- 통과 조건: local worker/live adapter py_compile, focused unit tests, Next typecheck, DTO example/page markers, docs, roadmap, AGENTS current task, verification script reference가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_live_scheduler_host_activation_execution_final_preflight.sh`
- 무엇을 증명하는가: approved host activation execution decision 이후에도 reviewed plan, execution request, command preview consistency, fresh runtime readiness를 다시 검증하고, 통과해도 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: execution final preflight py_compile, operations env parser/CLI tests, approve/deny/runtime-readiness reports, command preview drift rejection, secret non-leakage, repo-inside decision/env/plan/output refusal, thin wrapper delegation to `stockanalysis.operations.cli`, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_data_operations_live_scheduler_host_activation_execution.sh`
- 무엇을 증명하는가: execution final preflight 이후 missing/confirm/abort host mutation confirmation record를 검증하되, Codex task 안에서는 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: host activation execution py_compile, unit tests, missing/confirm/abort reports, secret non-leakage, mismatched confirmation/repo-inside path refusal, thin wrapper delegation to `stockanalysis.operations.cli`, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_manual_host_scheduler_activation_explicit_approval.sh`
- 무엇을 증명하는가: confirmed host activation execution report 이후 exact execution/rollback command approval packet을 만들고 approve/abort records를 검증하되, Codex task 안에서는 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: manual host scheduler activation approval py_compile, CLI tests, missing/approve/abort reports, exact command drift rejection, secret non-leakage, repo-inside path refusal, thin wrapper delegation to `stockanalysis.operations.cli`, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_manual_host_scheduler_activation_preflight.sh`
- 무엇을 증명하는가: approved exact-command packet과 fresh runtime env readiness를 함께 검증하되, Codex task 안에서는 `launchctl`이나 host LaunchAgents write를 실행하지 않는지 확인한다.
- 통과 조건: manual host scheduler activation preflight py_compile, CLI tests, passed/blocked reports, runtime env failure block, secret non-leakage, repo-inside path refusal, thin wrapper delegation to `stockanalysis.operations.cli`, docs, roadmap, AGENTS next task, AWH task verify가 모두 통과한다.

- 명령: `bash scripts/verify_apps_web_scaffold.sh`
- 무엇을 증명하는가: `apps/web` Next.js App Router scaffold가 fixture server payload를 읽는 read-only investment cockpit shell로 동작하는지 확인한다.
- 통과 조건: web scaffold files, npm install, TypeScript check, Next production build, fixture server runtime, Next production server route smoke for `/`, `/remediation`, `/data-health`, `/cycles`, frontend architecture/API/adapter/fixture server regression checks가 모두 통과한다.

- 명령: `bash scripts/verify_frontend_detail_routes.sh`
- 무엇을 증명하는가: event, theme, performance, recommendation, thesis, portfolio coverage, AI evidence, source document detail routes가 fixture server payload를 읽고 read-only Server Component로 렌더링되는지 확인한다.
- 통과 조건: detail route files, npm install, TypeScript check, Next production build, fixture server runtime, Next production server route smoke for `/events`, `/themes/ANNUAL_REPORTING`, `/performance`, `/recommendations/AAPL-2024-11-01`, `/theses/AAPL-bootstrap-v1`, `/portfolio/coverage`, `/ai-evidence/sec-event-aapl-10k-20240928`, `/source-documents/aapl-2024-10k-20240928`, frontend fixture server regression check가 모두 통과한다.

- 명령: `bash scripts/verify_migrations.sh`
- 무엇을 증명하는가: 현재 작성된 Postgres migration skeleton이 실제 임시 Postgres 인스턴스에 순서대로 적용되는지 검증한다.
- 통과 조건: 모든 migration이 에러 없이 적용되고, 기대 schema의 테이블 목록이 출력된다.

- 명령: `bash scripts/verify_seed_bootstrap.sh`
- 무엇을 증명하는가: migration 이후 최소 reference/data_source seed가 실제로 적재되는지 검증한다.
- 통과 조건: seed SQL이 에러 없이 적용되고 `ref.market`, `ref.exchange`, `ingest.data_source` row count가 출력된다.

- 명령: `bash scripts/verify_ingest_bootstrap.sh`
- 무엇을 증명하는가: ingest bootstrap 코드가 import/compile 가능하고, 기본 CLI와 request builder가 동작하는지 검증한다.
- 통과 조건: `compileall`, `unittest`, `list-sources`, `build-request` dry-run이 모두 성공한다.

- 명령: `bash scripts/verify_macro_ingest.sh`
- 무엇을 증명하는가: macro ingest 코드가 import/compile 가능하고, fixture 기반 FRED 정규화와 SQL output 생성이 동작하는지 검증한다.
- 통과 조건: `compileall`, 전체 `unittest`, `macro-default-series`, fixture 기반 `macro-sync`, SQL output file 생성이 모두 성공한다.

- 명령: `bash scripts/verify_macro_upsert_runner.sh`
- 무엇을 증명하는가: fixture 기반 macro payload가 canonical Postgres에 실제 upsert되고 `ops.pipeline_run`, `macro.series`, `macro.observation`이 기대 상태로 남는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `macro-upsert`, pipeline run status 확인, macro row count 확인이 모두 성공한다.

- 명령: `bash scripts/verify_macro_batch_upsert.sh`
- 무엇을 증명하는가: 여러 기본 macro series가 fixture directory 기반으로 canonical Postgres에 순차 적재되고 series별 `pipeline_run`이 남는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, 2-series `macro-batch-upsert`, macro row count 2건, observation row count 5건, linked `source_run_id` 5건, succeeded `pipeline_run` 2건이 모두 확인된다.

- 명령: `bash scripts/verify_macro_run_history_report.sh`
- 무엇을 증명하는가: batch upsert 이후 `macro-run-history`가 최근 run 목록과 status 집계, per-run observation count를 올바르게 반환하는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, 2-series batch upsert, `macro-run-history` JSON에서 run_count 2건, succeeded status count 2건, run별 observation count가 기대값으로 확인된다.

- 명령: `bash scripts/verify_sec_filings_ingest.sh`
- 무엇을 증명하는가: SEC submissions fixture가 filing metadata로 정규화되어 `ingest.source_document`에 실제 upsert되고 `ingested_by_run_id`와 `ops.pipeline_run`이 연결되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, fixture 기반 `sec-filings-upsert`, `source_document` 2건, non-null `ingested_by_run_id` 2건, latest `sec_filings_upsert` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_sec_filing_raw_fetch.sh`
- 무엇을 증명하는가: 기존 SEC filing metadata row에 raw filing artifact가 실제로 저장되고 `raw_storage_uri`, `checksum`, `ops.pipeline_run`이 기대 상태로 남는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, fixture 기반 `sec-filings-upsert`, fixture 기반 `sec-filing-raw-fetch`, `raw_storage_uri`와 `checksum` 반영 1건, latest `sec_filing_raw_fetch` run status 성공, artifact file 1건 생성 확인이 모두 통과한다.

- 명령: `bash scripts/verify_sec_filings_event_extract.sh`
- 무엇을 증명하는가: raw SEC filing artifact에서 heuristic event가 생성되고 `event.event_document_link`와 `ops.pipeline_run`이 기대 상태로 남는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, fixture 기반 `sec-filings-upsert`, fixture 기반 `sec-filing-raw-fetch`, fixture 기반 `sec-filings-event-extract`, linked `event.event` 1건, dedupe key 1건, latest `sec_filings_event_extract` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_sec_filings_event_batch_extract.sh`
- 무엇을 증명하는가: pending SEC raw filings 2건이 batch로 event화되고 `event.event_document_link`, dedupe key, per-document pipeline run이 기대 상태로 남는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, fixture 기반 `sec-filings-upsert`, 2건 fixture 기반 `sec-filing-raw-fetch`, `sec-filings-event-batch-extract`, linked event 2건, annual/quarterly dedupe key 각 1건, succeeded `sec_filings_event_extract` run 2건이 모두 확인된다.

- 명령: `bash scripts/verify_event_classification_impact_bootstrap.sh`
- 무엇을 증명하는가: pending SEC events가 minimal internal theme taxonomy와 `event.event_classification_impact`에 실제로 연결되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, 2건 SEC event 생성, classification node 5건, hierarchy edge 4건, classification impact 2건, annual/quarterly mapping 각 1건, latest `event_classification_impact_bootstrap` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_event_instrument_impact_bootstrap.sh`
- 무엇을 증명하는가: pending SEC events가 canonical issuer/instrument exact-match lookup을 통해 `event.event_instrument_impact`에 실제로 연결되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, 2건 SEC event 생성, canonical Apple issuer/instrument insert, instrument impact 2건, annual/quarterly AAPL mapping 각 1건, latest `event_instrument_impact_bootstrap` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_sec_companyfacts_ingest.sh`
- 무엇을 증명하는가: selected SEC companyfacts facts가 canonical instrument에 연결되어 `market.financial_statement_period`, `market.financial_metric_value`에 실제로 적재되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, SEC filing metadata ingest, canonical Apple issuer/instrument insert, period row 2건, metric row 4건, linked `source_document_id` 2건, annual revenue 1건, quarterly net income 1건, latest `sec_companyfacts_upsert` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_market_price_ingest.sh`
- 무엇을 증명하는가: selected daily adjusted price bars가 canonical instrument에 연결되어 `market.daily_price_bar`에 실제로 적재되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, canonical Apple issuer/instrument insert, daily bar 2건, latest adjusted close 1건, latest volume 1건, non-null `source_run_id` 2건, latest `market_price_upsert` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_market_price_batch_ingest.sh`
- 무엇을 증명하는가: 여러 symbol의 daily adjusted price bars가 canonical instrument에 연결되어 `market.daily_price_bar`에 batch 적재되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, canonical Apple/Microsoft issuer/instrument insert, daily bar 4건, AAPL 2건, MSFT 2건, non-null `source_run_id` 4건, succeeded `market_price_upsert` run 2건이 모두 확인된다.

- 명령: `bash scripts/verify_market_universe_bootstrap.sh`
- 무엇을 증명하는가: SEC ticker/exchange sample payload가 supported exchange filter를 거쳐 canonical `ref.issuer`, `ref.instrument`에 실제로 bootstrap되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, fixture 기반 `market-universe-bootstrap`, issuer 2건, instrument 2건, `AAPL -> XNAS` 1건, `BABA -> XNYS` 1건, unsupported `BAESY` 0건, latest `market_universe_bootstrap` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_market_price_universe_backfill.sh`
- 무엇을 증명하는가: canonical universe bootstrap 이후 active symbol list를 읽어 batch daily price backfill이 실제로 동작하는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, fixture 기반 `market-universe-bootstrap`, fixture 기반 `market-price-universe-backfill`, daily bar 4건, `AAPL` 2건, `BABA` 2건, non-null `source_run_id` 4건, succeeded `market_price_upsert` run 2건이 모두 확인된다.

- 명령: `bash scripts/verify_strategy_universe_slicing.sh`
- 무엇을 증명하는가: canonical universe와 daily price bars를 이용해 strategy-specific universe snapshot이 `signal.strategy_universe_batch/member`에 실제로 생성되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, fixture 기반 `market-universe-bootstrap`, fixture 기반 `market-price-universe-backfill`, fixture 기반 `strategy-universe-slice`, strategy universe batch 1건, member 2건, `AAPL` rank 1, `BABA` rank 2, non-null `source_run_id` 1건, latest `strategy_universe_slice` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_ai_intelligence_architecture.sh`
- 무엇을 증명하는가: AI intelligence architecture의 최소 DB boundary가 실제 Postgres에 적용되고 prompt/model invocation/chunk/embedding/extraction/eval metadata를 저장할 수 있는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `ai` schema tables 6개 존재, 샘플 `ai.prompt_template`, `ai.model_invocation`, `ai.document_chunk`, `ai.embedding_index`, `ai.extraction_artifact`, `ai.eval_run` row 생성이 모두 확인된다.

- 명령: `bash scripts/verify_event_intelligence_llm_extract.sh`
- 무엇을 증명하는가: SEC raw filing artifact에서 structured AI event metadata와 canonical event가 함께 저장되는 첫 AI 런타임 경로가 실제로 동작하는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, SEC metadata upsert, SEC raw fetch, `event-intelligence-llm-extract`, canonical event 1건, `ai.model_invocation` 1건, `ai.document_chunk` 1건, `ai.extraction_artifact` 1건, latest `event_intelligence_llm_extract` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_market_feature_snapshot.sh`
- 무엇을 증명하는가: strategy universe snapshot 이후 deterministic market feature snapshot이 실제 Postgres에 저장되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `market-universe-bootstrap`, `market-price-universe-backfill`, `strategy-universe-slice`, `market-feature-snapshot`, feature definition 5건, feature row 10건, `AAPL latest_adjusted_close`, `BABA return_1d`, latest `market_feature_snapshot` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_instrument_theme_enrichment.sh`
- 무엇을 증명하는가: selected strategy universe instruments가 existing event impacts를 통해 internal theme memberships로 실제 연결되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `market-universe-bootstrap`, `market-price-universe-backfill`, `strategy-universe-slice`, SEC event extract, classification/instrument impact bootstrap, `instrument-theme-enrichment`, `AAPL -> ANNUAL_REPORTING` membership 1건, derived theme total 1건, linked source document 1건, latest `instrument_theme_enrichment` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_cycle_state_snapshot.sh`
- 무엇을 증명하는가: selected internal theme nodes가 deterministic feature snapshot과 recent event heat를 바탕으로 `signal.cycle_state_snapshot`에 실제 저장되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `market-universe-bootstrap`, `market-price-universe-backfill`, `strategy-universe-slice`, `market-feature-snapshot`, SEC event extract, classification/instrument impact bootstrap, `instrument-theme-enrichment`, `cycle-state-snapshot`, `ANNUAL_REPORTING` snapshot 1건, `cycle_state = forming`, `cycle_score = 0.2075`, latest `cycle_state_snapshot` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_recommendation_bootstrap.sh`
- 무엇을 증명하는가: selected strategy universe, deterministic feature, direct theme membership, cycle state가 recommendation batch와 recommendation rows로 실제 저장되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `market-universe-bootstrap`, `market-price-universe-backfill`, `strategy-universe-slice`, `market-feature-snapshot`, SEC event extract, classification/instrument impact bootstrap, `instrument-theme-enrichment`, `cycle-state-snapshot`, `recommendation-bootstrap`, recommendation batch 1건, AAPL recommendation 1건, bucket `watch`, action `watch`, total score `0.3610`, latest `recommendation_bootstrap` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_recommendation_score_component.sh`
- 무엇을 증명하는가: recommendation total score를 구성하는 component score와 weight가 canonical child table에 저장되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `market-universe-bootstrap`, `market-price-universe-backfill`, `strategy-universe-slice`, `market-feature-snapshot`, SEC event extract, classification/instrument impact bootstrap, `instrument-theme-enrichment`, `cycle-state-snapshot`, `recommendation-bootstrap`, `signal.recommendation_score_component` table 존재, recommendation 1건, component row 4건, AAPL weighted sum `0.3610`, latest `recommendation_bootstrap` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_thesis_bootstrap.sh`
- 무엇을 증명하는가: active recommendation rows가 deterministic investment thesis와 연결되어 thesis 근거와 무효화 조건을 저장하는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `market-universe-bootstrap`, `market-price-universe-backfill`, `strategy-universe-slice`, `market-feature-snapshot`, SEC event extract, classification/instrument impact bootstrap, `instrument-theme-enrichment`, `cycle-state-snapshot`, `recommendation-bootstrap`, `thesis-bootstrap`, active thesis 1건, AAPL recommendation의 non-null `thesis_id`, title `AAPL watch thesis via Annual Reporting`, conviction score `0.3610`, latest `thesis_bootstrap` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_thesis_review_bootstrap.sh`
- 무엇을 증명하는가: active investment thesis가 현재 linked recommendation/cycle evidence 기준으로 deterministic review row에 저장되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `market-universe-bootstrap`, `market-price-universe-backfill`, `strategy-universe-slice`, `market-feature-snapshot`, SEC event extract, classification/instrument impact bootstrap, `instrument-theme-enrichment`, `cycle-state-snapshot`, `recommendation-bootstrap`, `thesis-bootstrap`, `thesis-review-bootstrap`, `signal.thesis_review` table 존재, AAPL review action `watch`, health score `0.3610`, next review date `2024-12-01`, latest `thesis_review_bootstrap` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_review_bootstrap.sh`
- 무엇을 증명하는가: current paper portfolio position snapshot이 thesis review와 recommendation evidence 기준으로 deterministic portfolio review header/item rows에 저장되고, optional outcome coverage gate가 missing thesis/outcome/weight blind spot을 review action/risk에 반영하는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `market-universe-bootstrap`, `market-price-universe-backfill`, `strategy-universe-slice`, `market-feature-snapshot`, SEC event extract, classification/instrument impact bootstrap, `instrument-theme-enrichment`, `cycle-state-snapshot`, `recommendation-bootstrap`, `thesis-bootstrap`, `thesis-review-bootstrap`, `portfolio-position-snapshot-upsert`, `portfolio-review-bootstrap`, `portfolio.review` table 존재, `portfolio.review_item` table 존재, AAPL review item action `monitor`, health score `0.3610`, current weight `0.0500`, latest `portfolio_review_bootstrap` run status 성공, coverage gate rerun에서 AAPL `monitor` with `covered`, BABA `needs_thesis_review` with `missing_thesis`, review item 2건이 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_review_run_history_report.sh`
- 무엇을 증명하는가: 최근 portfolio review runs와 action/risk/attention item 운영 리포트가 canonical Postgres에서 read-only JSON으로 조회되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, universe/price/event/theme/recommendation/thesis/review/outcome/position pipeline, coverage-gated `portfolio-review-bootstrap`, `portfolio-review-run-history`, review count 1건, risk count `watch:1`, action count `monitor:1`, action count `needs_thesis_review:1`, attention item count 1건, BABA attention action `needs_thesis_review`, BABA reason의 `coverage status missing_thesis`가 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_remediation_queue_report.sh`
- 무엇을 증명하는가: portfolio review attention item이 remediation type, suggested runner, next step을 포함한 read-only queue JSON으로 조회되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, universe/price/event/theme/recommendation/thesis/review/outcome/position pipeline, coverage-gated `portfolio-review-bootstrap`, `portfolio-remediation-queue`, queue item count 1건, remediation type count `thesis_remediation:1`, action count `needs_thesis_review:1`, BABA item의 suggested runner `thesis_or_position_link_review`, BABA reason의 `coverage status missing_thesis`가 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_remediation_ticket_bootstrap.sh`
- 무엇을 증명하는가: portfolio review attention item이 persistent `portfolio.remediation_ticket` row로 upsert되고 중복 실행해도 duplicate ticket이 생기지 않는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, universe/price/event/theme/recommendation/thesis/review/outcome/position pipeline, coverage-gated `portfolio-review-bootstrap`, `portfolio-remediation-ticket-bootstrap` 2회 실행, BABA `needs_thesis_review` ticket 1건, status `open`, remediation type `thesis_remediation`, suggested runner `thesis_or_position_link_review`, DB ticket count 1건, succeeded `portfolio_remediation_ticket_bootstrap` pipeline run 2건이 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_remediation_ticket_report.sh`
- 무엇을 증명하는가: persistent remediation ticket이 status/action/remediation type/suggested runner metadata를 포함한 read-only 운영 report로 조회되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, universe/price/event/theme/recommendation/thesis/review/outcome/position pipeline, coverage-gated `portfolio-review-bootstrap`, `portfolio-remediation-ticket-bootstrap`, `portfolio-remediation-ticket-report`, BABA open ticket 1건, status count `open:1`, remediation type count `thesis_remediation:1`, action count `needs_thesis_review:1`, source run status `succeeded`, BABA reason의 `coverage status missing_thesis`가 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_remediation_ticket_update.sh`
- 무엇을 증명하는가: persistent remediation ticket status를 lifecycle command로 변경하고, resolved/ignored 계열 상태에 `resolved_at`을 기록하는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, universe/price/event/theme/recommendation/thesis/review/outcome/position pipeline, coverage-gated `portfolio-review-bootstrap`, `portfolio-remediation-ticket-bootstrap`, open ticket report, `portfolio-remediation-ticket-update --status resolved`, resolved report에서 BABA status `resolved`, non-null `resolved_at`, open report ticket count 0건이 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_remediation_daily_automation.sh`
- 무엇을 증명하는가: daily portfolio remediation runner가 review bootstrap, ticket bootstrap, ticket report를 순서대로 실행하고 top-level pipeline provenance를 남기는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, universe/price/event/theme/recommendation/thesis/outcome/position prerequisite pipeline, `portfolio-remediation-daily-run`, coverage-gated review item 2건, BABA open ticket 1건, remediation type `thesis_remediation`, suggested runner `thesis_or_position_link_review`, latest `portfolio_remediation_daily_automation` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_remediation_scheduler_contract.sh`
- 무엇을 증명하는가: actual scheduler activation 전 실행 주기, alert, artifact, retry, rollback contract가 문서화되어 있고 repo-local scheduler activation artifact가 생성되지 않았는지 검증한다.
- 통과 조건: scheduler contract docs, task contract, loop contract, handoff, review가 존재하고, `portfolio-remediation-daily-run`, `America/New_York`, `Artifact Policy`, `Alert Policy`, `Retry Policy`, `Rollback Policy`, `Activation Gate`가 문서화되어 있으며, cron/launchd/GitHub Actions scheduler activation artifact가 없는 것이 확인된다.

- 명령: `bash scripts/verify_portfolio_remediation_scheduler_activation.sh`
- 무엇을 증명하는가: actual scheduler가 나중에 호출할 repo-local wrapper가 required env, artifact root, preflight mode, no-scheduler-install boundary를 검증하는지 확인한다.
- 통과 조건: wrapper/verify script syntax 통과, missing required env failure 확인, temp artifact root preflight success, preflight JSON shape와 skip metadata 확인, cron/launchd/GitHub Actions scheduler activation artifact 부재 확인이 모두 통과한다.

- 명령: `bash scripts/verify_portfolio_remediation_scheduler_holiday_skip.sh`
- 무엇을 증명하는가: scheduler wrapper가 explicit skip date hit에서 DB runner를 호출하지 않고 skip artifact를 남기는지 확인한다.
- 통과 조건: wrapper/verify script syntax 통과, invalid DB command에서도 skip date hit success, JSON/stderr artifact 생성, skip payload `portfolio_remediation_scheduler_skip`, `status=skipped`, configured reason/run date/as-of date/skip dates 확인, preflight skip metadata 확인이 모두 통과한다.

- 명령: `bash scripts/verify_portfolio_remediation_scheduler_install.sh`
- 무엇을 증명하는가: macOS launchd scheduler install artifact가 dry-run으로 안전하게 렌더링되고 host scheduler path를 쓰지 않는지 확인한다.
- 통과 조건: install script syntax 통과, scheduler wrapper syntax 통과, temp env file 기반 dry-run success, rendered plist에 label/env file/wrapper path/working directory/Monday-Friday 18:30 schedule 포함, dry-run output이 host LaunchAgents 경로가 아님이 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_remediation_scheduler_runtime_smoke.sh`
- 무엇을 증명하는가: scheduler wrapper run mode가 Docker Postgres runtime에서 daily remediation runner를 실행하고 JSON/stderr artifact와 succeeded DB pipeline run을 남기는지 확인한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, universe/price/event/theme/recommendation/thesis/outcome/position prerequisite pipeline, scheduler wrapper run mode, stdout JSON artifact 1건, stderr log artifact 1건, BABA open remediation ticket 1건, latest `portfolio_remediation_daily_automation` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_remediation_scheduler_env_readiness.sh`
- 무엇을 증명하는가: scheduler env template과 readiness checker가 production secret 없이 env file gate를 검증하는지 확인한다.
- 통과 조건: renderer/checker/wrapper/install syntax 통과, repo 내부 template output 거부, unedited template readiness failure, valid temp env readiness success, install dry-run compatibility가 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_remediation_scheduler_runtime_env_smoke.sh`
- 무엇을 증명하는가: trusted env file을 source하는 runtime smoke runner가 scheduler wrapper를 실행하고 artifact, BABA remediation ticket, latest DB run status를 검증하는지 확인한다.
- 통과 조건: 전체 `unittest`, runner/wrapper syntax 통과, docker Postgres migration/seed, prerequisite pipeline, temp env file 기반 `scripts/smoke_portfolio_remediation_scheduler_runtime_env.sh --env-file`, stdout summary `runtime_env_smoke=passed`, JSON/stderr artifact 존재, BABA open `thesis_remediation` ticket, latest `portfolio_remediation_daily_automation` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_position_snapshot_ingest.sh`
- 무엇을 증명하는가: 표준 CSV position snapshot이 canonical portfolio tables에 저장되고 active thesis와 연결되며 downstream portfolio review 입력으로 사용되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, `market-universe-bootstrap`, `market-price-universe-backfill`, `strategy-universe-slice`, `market-feature-snapshot`, SEC event extract, classification/instrument impact bootstrap, `instrument-theme-enrichment`, `cycle-state-snapshot`, `recommendation-bootstrap`, `thesis-bootstrap`, `thesis-review-bootstrap`, CSV 기반 `portfolio-position-snapshot-upsert`, paper portfolio 1건, AAPL position snapshot 1건, linked active thesis 1건, latest `portfolio_position_snapshot_upsert` run status 성공, downstream portfolio review item action `monitor`가 모두 확인된다.

- 명령: `bash scripts/verify_performance_outcome_bootstrap.sh`
- 무엇을 증명하는가: 추천과 thesis의 사후 가격 성과가 performance schema에 저장되고 pipeline run과 연결되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, benchmark 포함 `market-universe-bootstrap`, `market-price-universe-backfill`, `strategy-universe-slice`, `market-feature-snapshot`, SEC event extract, classification/instrument impact bootstrap, `instrument-theme-enrichment`, `cycle-state-snapshot`, `recommendation-bootstrap`, `thesis-bootstrap`, `thesis-review-bootstrap`, outcome fixture 기반 `market-price-upsert`, `performance-outcome-batch-bootstrap`, `performance.recommendation_outcome` 2건, `performance.thesis_outcome` 2건, 2024-11-04 AAPL absolute return `0.010000`, SPY benchmark return `0.005000`, alpha `0.005000`, 2024-12-02 AAPL absolute return `0.100000`, SPY benchmark return `0.040000`, alpha `0.060000`, recommendation outcome label `outperform`, thesis success grade `pass`, latest `performance_outcome_bootstrap` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_scheduled_outcome_runner.sh`
- 무엇을 증명하는가: due date와 horizon days를 기준으로 아직 outcome이 없는 recommendation batch/horizon을 찾아 기존 outcome runner를 자동 실행하는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, benchmark 포함 universe/price/event/theme/recommendation/thesis pipeline, outcome fixture 기반 `market-price-upsert`, `performance-outcome-schedule-bootstrap`, `performance.recommendation_outcome` 2건, `performance.thesis_outcome` 2건, 2024-11-04 AAPL alpha `0.005000`, 2024-12-02 AAPL alpha `0.060000`, child `performance_outcome_bootstrap` succeeded run 2건, parent `performance_outcome_schedule_bootstrap` latest status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_attribution_bootstrap.sh`
- 무엇을 증명하는가: portfolio position snapshot과 thesis outcome이 연결되어 security/theme/cash attribution component로 저장되고 pipeline run과 연결되는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, benchmark 포함 universe/price/event/theme/recommendation/thesis/outcome/position pipeline, `portfolio-attribution-bootstrap`, `performance.attribution_run` 1건, `performance.attribution_component` 3건, AAPL security selection contribution `30.0000` bps, `ANNUAL_REPORTING` theme exposure contribution `30.0000` bps, `CASH` cash timing weight `0.9500`, contribution `0.0000` bps, latest `portfolio_attribution_bootstrap` run status 성공이 모두 확인된다.

- 명령: `bash scripts/verify_portfolio_outcome_coverage_report.sh`
- 무엇을 증명하는가: portfolio attribution에서 제외될 수 있는 missing thesis/outcome/weight position을 read-only coverage report로 식별하고 count/weight/cash coverage를 계산하는지 검증한다.
- 통과 조건: 전체 `unittest`, docker Postgres migration/seed, benchmark 포함 universe/price/event/theme/recommendation/thesis/outcome/position pipeline, `portfolio-outcome-coverage-report`, position count 2건, AAPL `covered`, BABA `missing_thesis`, covered weight `0.0500`, missing thesis weight `0.0300`, total position weight `0.0800`, cash weight `0.9200`, count coverage ratio `0.5000`, weight coverage ratio `0.6250`이 모두 확인된다.

## Manual Checks

- 시나리오: `docs/project-foundation.md`를 읽고 시스템 아키텍처가 데이터, 이벤트, 테마/섹터 그래프, 사이클 엔진, thesis 엔진, 추천 엔진, 포트폴리오 검토, 성과 분석을 모두 포함하는지 검토한다.
- 기대 동작: 프로젝트 목표와 범위가 단순 추천 앱이 아니라 사이클 기반 투자 운영 시스템으로 일관되게 정의되어 있다.

- 시나리오: `docs/agent-work-harness-evaluation.md`를 읽고 하네스 도입 범위가 `Level 1 중심 부분 도입`으로 정리되어 있는지 검토한다.
- 기대 동작: full harness 즉시 도입이 아니라 repo-level 문서와 task-level contract/handoff 중심 도입이라는 판단이 명확하다.

- 시나리오: `docs/ai-intelligence-architecture.md`를 읽고 AI가 추천 결정자가 아니라 문서 해석, 이벤트 구조화, thesis/review/report 생성을 맡는지 검토한다.
- 기대 동작: RAG와 ontology를 병행하되 초기에는 Postgres graph tables와 vector metadata adapter로 시작하고, token/cost/quality governance가 명시되어 있다.

## Browser Or Runtime Checks

- URL, route, job, endpoint: `http://127.0.0.1:8765/__health`, `http://127.0.0.1:8765/__endpoints`, `http://127.0.0.1:8765/api/dashboard/today`, `http://127.0.0.1:8765/api/events?asOfDate=2024-11-01`, `http://127.0.0.1:8765/api/themes/ANNUAL_REPORTING?asOfDate=2024-11-01`, `http://127.0.0.1:8765/api/performance/Long%20Term%20Paper/outcomes?measurementEndDate=2024-12-02`, `http://127.0.0.1:3000/`, `http://127.0.0.1:3000/remediation`, `http://127.0.0.1:3000/data-health`, `http://127.0.0.1:3000/cycles`, `http://127.0.0.1:3000/events`, `http://127.0.0.1:3000/themes/ANNUAL_REPORTING`, `http://127.0.0.1:3000/performance`, `http://127.0.0.1:3000/recommendations/AAPL-2024-11-01`, `http://127.0.0.1:3000/theses/AAPL-bootstrap-v1`, `http://127.0.0.1:3000/portfolio/coverage`, `http://127.0.0.1:3000/ai-evidence/sec-event-aapl-10k-20240928`, `http://127.0.0.1:3000/source-documents/aapl-2024-10k-20240928`
- 수행 경로: `bash scripts/verify_frontend_fixture_server.sh`가 fixture server runtime smoke를 수행하고, `bash scripts/verify_apps_web_scaffold.sh`와 `bash scripts/verify_frontend_detail_routes.sh`가 Next production server route smoke를 수행한다.
- 확인할 증거: health payload, endpoint index, daily cockpit fixture payload, event/theme/performance fixture payload, remediation ticket query-string fixture payload, 404/405 error payload, web route HTML content가 검증된다.

- URL, route, job, endpoint: `http://127.0.0.1:3006/`, `http://127.0.0.1:3006/events`, `http://127.0.0.1:3006/themes/ANNUAL_REPORTING`, `http://127.0.0.1:3006/performance`, `http://127.0.0.1:3006/portfolio/coverage`
- 수행 경로: `agent-browser`로 production Next server를 열고 screenshot, console, errors를 확인한다.
- 확인할 증거: `docs/tasks/frontend-browser-visual-qa/report.md`와 `output/playwright/frontend-browser-visual-qa/screenshots/`의 local browser evidence가 존재한다. 모바일 `/performance`는 `clientWidth=390`, `scrollWidth=390`으로 horizontal overflow가 없어야 한다.

## Metrics Or Logs

- metric 또는 로그 소스: 하네스 검증 명령 출력, 향후 백테스트 결과 로그, 추천/리뷰 이력
- 기대 임계값 또는 신호: 현재 단계에서는 문서 검증 통과가 최소 신호이며, 구현 단계부터는 추천 정확도보다 재현 가능성과 평가 일관성을 우선한다.

## Regression Guard

- 유지되어야 하는 기존 동작: 프로젝트 정체성은 단순 단기 종목 추천기가 아니라 섹터/테마 사이클 기반 중장기 투자 운영 시스템이어야 한다.
- 그것을 지키는 체크: `docs/project-foundation.md`와 `AGENTS.md`에서 LLM 역할, 추천 기록 원칙, 검토 중심 구조가 계속 유지되는지 문서 diff와 수동 검토로 확인한다.

## Rollback

- 실패 시 끄거나 되돌리는 방법: 새 아키텍처 또는 워크플로 문서가 혼란을 만들면 해당 task에서 추가된 문서만 되돌리고, repo-level 하네스는 유지한 채 내용을 더 단순한 운영 규칙으로 축소한다.

## Human Confirmation

- 여전히 사람이 판단해야 하는 항목: 초기 시장 범위를 미국과 한국 중 어디로 제한할지
- 여전히 사람이 판단해야 하는 항목: 추천 대상 유니버스를 어떤 기준으로 100~300개로 정의할지
- 여전히 사람이 판단해야 하는 항목: 이후 실거래 연동을 정말 목표로 둘지, 연구/의사결정 지원 시스템으로 제한할지
