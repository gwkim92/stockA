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
- 통과 조건: `docs/project-execution-roadmap.md`, `docs/tasks/project-execution-roadmap/` 문서, AGENTS repo map, 완료된 `frontend-runtime-db-smoke`, immediate next task `frontend-api-server-framework-decision`, API runtime guardrail이 모두 확인된다.

- 명령: `bash scripts/verify_frontend_architecture.sh`
- 무엇을 증명하는가: investment cockpit 방향, route map, API boundary, AI boundary, security boundary, phased implementation, fixture-only `apps/web` scaffold가 문서와 파일로 정렬되어 있는지 확인한다.
- 통과 조건: `docs/frontend-architecture.md`와 task docs가 존재하고, frontend doc에 cockpit, route map, data boundary, AI boundary, security boundary, implementation phases가 포함되며, `apps/web` scaffold가 존재하고 root-level `app` scaffold는 없는 것이 확인된다.

- 명령: `bash scripts/verify_frontend_api_contract.sh`
- 무엇을 증명하는가: daily cockpit, remediation tickets, data health, cycle state, recommendation detail, thesis detail, portfolio coverage, performance outcomes, AI evidence, source document, event list, theme detail read DTO contract와 example JSON이 고정되었는지 확인한다.
- 통과 조건: `docs/frontend-api-contract.md`, `docs/api/frontend/contract-index.json`, twelve example JSON이 존재하고, contract version과 endpoint/example mapping, common response shape, 핵심 field assertions가 모두 통과하며, root-level `app` scaffold가 없는 것이 확인된다.

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
