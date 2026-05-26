# Repository Working Map

## Purpose

이 저장소의 목적은 거시경제, 정치, 기술, 산업, 기업 흐름을 지속적으로 해석하고 섹터/테마 사이클을 추적하여 중장기 투자 thesis, 추천, 보유 검토, 성과 분석을 지원하는 AI 기반 투자 운영 시스템을 개발, 유지보수, 검증하는 것이다.

에이전트는 아래를 우선한다.

- 낙관보다 정확성
- 큰 수정보다 작고 검토 가능한 변경
- 완료 주장보다 검증 증거

## Repository Map

- Python backend/runtime: `src/stockanalysis/`
- Data/API ingest: `src/stockanalysis/ingest/`
- Signal, thesis, portfolio review: `src/stockanalysis/signal/`
- Performance and attribution: `src/stockanalysis/performance/`
- Frontend read adapters and local runtime: `src/stockanalysis/frontend/`
- Data operations backend orchestration: `src/stockanalysis/operations/`
- Next.js cockpit shell: `apps/web/`
- Postgres schema and seed: `db/migrations/`, `db/seeds/`
- Tests and fixtures: `tests/`
- Verification and scheduler scripts: `scripts/`
- 문서와 설계 노트: `README.md`, `docs/project-foundation.md`, `docs/project-execution-roadmap.md`, `docs/agent-work-harness-evaluation.md`, `docs/verification-plan.md`, `docs/tasks/`
- 민감하거나 고위험인 경로: API 키, DB connection env, scheduler env files, 배포 설정, 향후 실거래 연동 파일

## Core Commands

- Python 단위 검증: `PYTHONPATH=src python3 -m unittest`
- Data operations backend CLI: `PYTHONPATH=src python3 -m stockanalysis.operations.cli --help`
- 전체 기능별 검증: `bash scripts/verify_<task>.sh`
- 하네스 검증: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task <task-slug>`
- 프로젝트 순서 검증: `bash scripts/verify_project_execution_roadmap.sh`
- frontend contract 검증: `bash scripts/verify_frontend_api_contract.sh`
- frontend local runtime 검증: `bash scripts/verify_frontend_fixture_server.sh`
- frontend detail route 검증: `bash scripts/verify_frontend_detail_routes.sh`
- Next.js 타입/빌드: `cd apps/web && npm run typecheck && npm run build`

## Boundaries

- 생성 파일은 명시적으로 요구될 때만 수정한다.
- 시크릿, 배포 설정, 과금 로직은 명시적 승인 없이 바꾸지 않는다.
- 각 작업은 자기 task directory 범위 안에서 상태를 관리한다.
- 위험한 기술 도입은 직접 치환보다 내부 어댑터와 파일럿 도입을 우선한다.
- 투자 추천 로직은 설명 가능한 규칙과 검증 가능한 평가 체계를 먼저 갖춘 뒤에만 고도화한다.
- 백테스트 기준, benchmark, schema, 평가용 데이터 분할은 명시 없이 바꾸지 않는다.
- 실거래 자동화는 별도 승인 전까지 범위 밖이다.

## Working Rules

- 현재 작업에 필요한 최소한의 문서만 읽는다.
- 멀티파일, 위험 작업, 장기 작업은 먼저 `docs/tasks/<task-slug>/contract.md`를 만든다.
- 세션을 끊기기 전 `docs/tasks/<task-slug>/handoff.md`를 갱신한다.
- 프로젝트 차원의 완료 기준은 `docs/verification-plan.md`로 판단한다.
- `docs/escalation-rules.md`가 있으면 planner, multi-agent, automation 승격 여부를 그 문서로 판단한다.
- UI 작업은 가능하면 실제 브라우저 경로로 검증한다.
- benchmark, schema, evaluation 기준을 건드리면 그 사실을 반드시 명시한다.
- LLM은 추천을 직접 결정하는 존재가 아니라 문서 해석, 이벤트 구조화, 리포트 생성 역할을 우선한다.
- 추천 또는 보유 판단은 당시 입력 데이터, 점수, thesis, 무효화 조건을 함께 저장하는 방향으로 설계한다.
- 문서 단계에서도 다음 구현 단계가 바로 이어질 수 있을 정도로 결정 사항을 명확히 남긴다.
- 진행 순서가 흔들릴 때는 `docs/project-execution-roadmap.md`를 우선 기준으로 삼고, 변경하려면 별도 task contract에 근거를 남긴다.
- 현재 고정된 immediate next task는 `segment-history-backfill-v1`이다. `professional-equity-analysis-foundation` 흐름에서 재무 정규화, financial forecast inputs, sum-of-the-parts valuation foundation, segment footnote evidence foundation, reported segment footnote parser foundation, segment-level SOTP inputs, segment-level SOTP valuation allocation, reported segment unit normalization, segment-specific SOTP assumptions, segment SOTP driver calibration, financial statement model detail, recommendation financial model waterfall integration, peer relative, valuation snapshot, valuation target range visibility, valuation model quality depth, industry positioning, equity research artifact, zero-weight fundamental components, coverage guardrail, outcome backfill, paper safety interlock, manual weight review report, recommendation professional decision waterfall, thesis lifecycle professional gates가 구현되었고, 추천 weight 변경은 별도 승인된 pilot-weight task 전까지 금지한다. 포트폴리오 리스크 budget 작업은 `portfolio-risk-budget-policy-v2`, `portfolio-risk-budget-guardrail-run`, `portfolio-risk-budget-paper-validation-integration`, `portfolio-risk-budget-frontend-guardrail-visibility`, `portfolio-risk-budget-benchmark-composition-v1`, `portfolio-risk-budget-benchmark-provider-import-v1`, `portfolio-risk-budget-drift-quality-audit`, `portfolio-risk-budget-full-holdings-source`, `portfolio-risk-budget-rebalance-candidate-review`, `portfolio-position-sizing-policy-v1`까지 완료되었다. 최신 EC2 증거는 SSGA SPY provider import `run_id=992`, guardrail rerun `run_id=993`, `eval_run_id=23`, `benchmark_drift.status=calculated`, coverage `0.9983782`, active share `0.77853213`, `/api/trading/readiness`와 `/api/portfolio/Long%20Term%20Paper/coverage`의 `rebalance_candidate_review.status=review_required`, candidate count `7`, top candidates `TSLA/MSFT/AAPL/NVDA/AMZN`, `/api/portfolio/Long%20Term%20Paper/coverage`의 `position_sizing_review.status=review_required`, candidate count `4`, reduce review count `3`, top reduction candidates `TSLA/MSFT/AAPL`, `/api/recommendations/recommendation-147`의 `professional_decision_waterfall.status=paper_validation_required`, step count `8`, `order_boundary=read_only_no_order`, `/api/theses/thesis-28`의 `professional_lifecycle_gates.status=complete`, gate count `8`, `order_boundary=read_only_no_order`, `/api/stocks/AAPL`의 `financial_statement_model.status=available`, metric count `14`, computed metric count `12`, data gap count `2`, `order_boundary=read_only_no_order`, `/api/recommendations/recommendation-151`의 `financial_statement_model.status=available`, metric count `14`, computed metric count `12`, data gap count `2`, `financial_quality.status=재무 모델 연결`, `score_policy=recommendation_weights_unchanged`, `order_boundary=read_only_no_order`, `valuation-model-quality-depth-v1` EC2 smoke의 `/api/stocks/NVDA`, `/api/recommendations/recommendation-151`, `/api/theses/thesis-5` `valuation_quality.status=review_required`, method count `3`, data gap count `0`, sensitivity count `3`, limitations count `2`, `order_boundary=read_only_no_order`, `financial-forecast-and-scenario-inputs-v1` EC2 smoke의 `financial-forecast-inputs-run` `run_id=1016`/`1027`, `valuation-snapshot-run` `run_id=1017`/`1028`, `forecast_row_count=285`, valuation `snapshot_count=52`, forecast evidence `status=available`, DCF/scenario `forecast_row_count=15`, `scenario_count=3`, 그리고 `sum-of-the-parts-valuation-foundation-v1` EC2 smoke의 `market.sum_of_parts_component`, `sum-of-parts-valuation-run` `run_id=1031`/`1033`, `valuation-snapshot-run` `run_id=1032`/`1034`, `component_row_count=45`, `sum_of_parts=16`, `/api/stocks/NVDA`, `/api/recommendations/recommendation-151`, `/api/theses/thesis-5` `sotp_evidence.status=available`, `sotp_component_count=3`, route text `SOTP 구성요소`, `recommendation_scoring_mutated=false`, `segment-footnote-extraction-foundation-v1` local verification의 `research.segment_footnote_evidence`, `segment-footnote-evidence-run`, SOTP segment evidence DTO/UI, `recommendation_scoring_mutated=false`, 그리고 `reported-segment-footnote-parser-v1` local verification의 `reported-segment-footnote-parser-run`, simple SEC HTML segment table parser, `reported_segment_metric` upsert, same-period `segment_data_gap` cleanup, `recommendation_scoring_mutated=false`, 그리고 `financial-period-source-document-linkage-v1` EC2 smoke의 `financial-period-source-linkage-run` `run_id=1042`, `raw_fetch_success_count=1`, DB `linked_periods=29`, `raw_sec_docs=1`, `linked_raw_periods=2`, parser follow-up `candidate_count=1`, `reported_segment_metric_count=0`, `recommendation_scoring_mutated=false`, 그리고 `reported-segment-parser-quality-v1` EC2 smoke의 `reported-segment-footnote-parser-run` `run_id=1059`, `reported_segment_metric_count=10`, `removed_stale_metric_count=10`, AAPL segment rows period `2025-09-27`, stale `2025-10-17` count `0`, `recommendation_scoring_mutated=false`, 그리고 `segment-level-sotp-inputs-v1` EC2 smoke의 `sum-of-parts-valuation-run` `run_id=1060`, `reported_segment_input_count=5`, `valuation-snapshot-run` `run_id=1061`, `/api/stocks/AAPL` `sotp_evidence.reported_segment_inputs` count `5`, first segment `Americas`, revenue `178353`, operating income `72480`, operating margin `0.4063850902423845`, route text `사업부별 실적 입력`, `score_policy=recommendation_weights_unchanged`, `order_boundary=read_only_no_order`, 그리고 `segment-level-sotp-valuation-allocation-v1` EC2 smoke의 `sum-of-parts-valuation-run` `run_id=1062`, `valuation-snapshot-run` `run_id=1063`, `/api/stocks/AAPL` `sotp_evidence.reported_segment_allocations` count `5`, first segment `Americas`, allocation basis `operating_income_share`, allocation weight `0.41257535135504364`, allocated base fair value `57.54485598738951`, allocation sum `1`, route text `사업부별 가치 배분`, `score_policy=recommendation_weights_unchanged`, `order_boundary=read_only_no_order`, 그리고 `reported-segment-unit-normalization-v1` EC2 smoke의 `reported-segment-footnote-parser-run` `run_id=1064`, `sum-of-parts-valuation-run` `run_id=1065`, `valuation-snapshot-run` `run_id=1066`, `/api/stocks/AAPL` first reported segment input `metric_unit=USD_millions_as_reported`, route text `백만 달러 단위`, `score_policy=recommendation_weights_unchanged`, `order_boundary=read_only_no_order`, 그리고 `segment-specific-sotp-assumptions-v1` EC2 smoke의 `sum-of-parts-valuation-run` `run_id=1067`, `valuation-snapshot-run` `run_id=1068`, `/api/stocks/AAPL` `reported_segment_assumptions` count `5`, first assumption `Americas`, `base_growth_rate=0.06`, `base_multiple=20.0`, `driver_label=고마진 현금창출 사업부`, route text `사업부별 가정`, `score_policy=recommendation_weights_unchanged`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`, 그리고 `segment-sotp-driver-calibration-v1` EC2 smoke의 `sum-of-parts-valuation-run` `run_id=1069`, `valuation-snapshot-run` `run_id=1070`, `/api/stocks/AAPL` `reported_segment_assumptions` count `5`, first assumption `Americas`, `driver_template_label=지역 수요·환율·채널 믹스`, `calibration_method=single_period_margin_share_template_proxy`, `history_period_count=1`, route text `동인 지역 수요`, `score_policy=recommendation_weights_unchanged`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`이다. EC2에서는 FastAPI/Next.js와 profile별 `systemd` scheduler가 운영 후보로 동작 중이며, `stockanalysis-mvp-20260520`의 현재 public IPv4는 `34.206.72.213`이다. Codex OAuth는 EC2 재로그인 후 실제 `cycle-community-ai-summary-v2-run --provider codex_oauth --execute` smoke가 `run_id=712`, `invocation_id=983`, `failed_summary_count=0`으로 성공했다. 새 data operations 작업은 shell orchestration을 늘리지 말고 `stockanalysis-operations` backend CLI/service boundary를 우선 사용한다. 추천 scoring weight와 실거래 자동화는 별도 승인 전까지 범위 밖이다.

## Definition Of Done

작업은 아래가 모두 충족될 때만 완료다.

- 요청한 변화가 실제로 존재한다
- 필요한 검증이 수행되었다
- 남은 위험과 미검증 영역이 적혀 있다
- 현재 task directory가 다음 사람이 이어받을 수 있을 만큼 갱신되어 있다
- 아키텍처 또는 규칙 변경이면 관련 설계 문서와 task handoff가 함께 갱신되어 있다
