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
- 이전 immediate next task였던 `professional-source-gap-prioritization-v1`은 완료되었고 현재 고정된 immediate next task는 `professional-source-gap-remediation-decision-v1`이다. `professional-equity-analysis-foundation` 흐름에서 재무 정규화, financial forecast inputs, sum-of-the-parts valuation foundation, segment footnote evidence foundation, reported segment footnote parser foundation, segment-level SOTP inputs, segment-level SOTP valuation allocation, reported segment unit normalization, segment-specific SOTP assumptions, segment SOTP driver calibration, financial statement model detail, recommendation financial model waterfall integration, peer relative, valuation snapshot, valuation target range visibility, valuation model quality depth, industry positioning, equity research artifact, zero-weight fundamental components, coverage guardrail, outcome backfill, paper safety interlock, manual weight review report, recommendation professional decision waterfall, thesis lifecycle professional gates, source-data blocker visibility, ETF/fund holdings-based analysis visibility, ETF/fund liquidity source evidence, ETF/fund expense ratio source evidence, ETF/fund NAV premium-discount source evidence, ETF/fund tracking difference source evidence, recommendation outcome calibration sample expansion, recommendation weight review horizon gate, recommendation outcome maturity monitor, recommendation outcome due cadence action, professional source gap prioritization이 구현되었고, 추천 weight 변경은 별도 승인된 pilot-weight task 전까지 금지한다. 포트폴리오 리스크 budget 작업은 `portfolio-risk-budget-policy-v2`, `portfolio-risk-budget-guardrail-run`, `portfolio-risk-budget-paper-validation-integration`, `portfolio-risk-budget-frontend-guardrail-visibility`, `portfolio-risk-budget-benchmark-composition-v1`, `portfolio-risk-budget-benchmark-provider-import-v1`, `portfolio-risk-budget-drift-quality-audit`, `portfolio-risk-budget-full-holdings-source`, `portfolio-risk-budget-rebalance-candidate-review`, `portfolio-position-sizing-policy-v1`까지 완료되었다. EC2에서는 FastAPI/Next.js와 profile별 `systemd` scheduler가 운영 후보로 동작 중이며, `stockanalysis-mvp-20260520`의 현재 public IPv4는 `34.206.72.213`이다. Codex OAuth는 EC2 재로그인 후 실제 `cycle-community-ai-summary-v2-run --provider codex_oauth --execute` smoke가 `run_id=712`, `invocation_id=983`, `failed_summary_count=0`으로 성공했다. 새 data operations 작업은 shell orchestration을 늘리지 말고 `stockanalysis-operations` backend CLI/service boundary를 우선 사용한다. 추천 scoring weight와 실거래 자동화는 별도 승인 전까지 범위 밖이다.
- 최신 segment history 증거는 EC2 `segment-history-backfill-run` parent `run_id=1086`, parser `run_id=1090`, SOTP `run_id=1091`, valuation `run_id=1092`, AAPL 4개 annual reported segment periods, 각 period 5개 clean segment labels, bad segment count `0`, `/api/stocks/AAPL` sum-of-parts method의 `reported_segment_input_count=5`, `reported_segment_assumption_count=5`, first assumption `Americas`, `calibration_method=multi_period_segment_trend_template`, `history_period_count=4`, `observed_revenue_cagr=0.01674948697333`, `observed_margin_change=0.03691828054287135`이다.
- 최신 segment coverage expansion 증거는 EC2 parent `run_id=1134`이며 AAPL은 `coverage_status=trend_backed`, `parsed_period_count=4`, `bad_segment_count=0`이고 ADI는 source/raw annual document 3개를 확보했지만 `coverage_status=unsupported_layout`, `unsupported_candidate_count=3`이다. 다음 작업은 ADI raw SEC artifact를 fixture로 삼아 deterministic parser layout support를 추가하는 것이다.
- 최신 reported segment parser layout 증거는 EC2 parent `run_id=1165`이며 AAPL은 `coverage_status=trend_backed`, `parsed_period_count=4`, `parsed_segment_count=5`, skip reason 없음, ADI는 `coverage_status=single_reportable_segment_no_disaggregated_segment_table`, raw document period `3`, generic `unsupported_layout_count=0`이다.
- 최신 segment coverage breadth 증거는 EC2 parent `run_id=1254`이며 selected symbols `AAPL/ADI/AEIS/ALAB/ARM/DIS/ELF/EROK/FANG/GILD`, status counts `trend_backed=4`, `single_reportable_segment_no_disaggregated_segment_table=3`, `unsupported_layout=1`, `missing_source_document_linkage=2`이다. `AEIS`는 후속 parser task에서 단일 보고 세그먼트로 분류되었고 ARM/EROK는 companyfacts/source linkage blocker로 분리한다.
- 최신 AEIS segment parser 증거는 EC2 coverage smoke `run_id=1317`이며 AAPL은 `trend_backed`, ADI와 AEIS는 `single_reportable_segment_no_disaggregated_segment_table`, `unsupported_layout_count=0`, `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`이다.
- 최신 ARM source-linkage 증거는 EC2 source linkage `run_id=1339`, coverage smoke `run_id=1416`이다. ARM은 `20-F` companyfacts support로 54 facts/8 periods가 적재됐고 parser cleanup 후 `coverage_status=single_reportable_segment_no_disaggregated_segment_table`, `arm_reported_segment_metric_count=0`, `unsupported_layout_count=0`이다. 남은 blocker는 EROK이며 SEC companyfacts가 `ffd` only/no financial statement facts 상태라 precise blocker classification이 필요하다.
- 최신 source-linkage remediation 증거는 EC2 breadth coverage `run_id=1452`이다. 10-symbol sample은 `trend_backed=4`, `single_reportable_segment_no_disaggregated_segment_table=5`, `sec_companyfacts_missing_us_gaap_facts=1`, `unsupported_layout_count=0`이며 EROK는 `source_linkage_blocker=sec_companyfacts_missing_us_gaap_facts`로 분류된다.
- 최신 professional coverage refresh 증거는 EC2 coverage refresh `run_id=1519`, post-decision refresh `run_id=1565`, recommendation component rerun `run_id=1579`, quality eval `run_id=1580`/`eval_run_id=25`이다. 최신 quality eval은 `quality_status=ready_for_weight_review`, professional coverage `39/45 = 0.866667`, outcome count `30`, `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`, `broker_submit_allowed=false`, `order_boundary=read_only_no_order`를 보고했다. `/stocks/SPY`와 `/recommendations/recommendation-157`은 `fund_company_financial_model_not_applicable`, `/stocks/EROK`은 `sec_companyfacts_missing_us_gaap_facts`, `/stocks/ARM`은 재무 모델 available과 polluted segment label 부재를 route smoke로 확인했다.
- 최신 ETF/fund analysis 증거는 EC2 commit `05cdd2a`이다. `/api/stocks/SPY`와 `/api/recommendations/recommendation-157`은 `fund_instrument_analysis.status=available`, `benchmark_source=ssga_spdr_spy_daily_holdings`, `holding_count=503`, `holdings_coverage_weight=0.9983782`, top holdings `NVDA/AAPL/MSFT/AMZN/GOOGL`, `liquidity.status=collected`, `liquidity.source_name=market.daily_price_bar`, `liquidity.observation_count=100`, 비용률 `collected`, 비용률 값 `0.000945`/`0.094500%`, 비용률 원천 `ssga_spdr_product_page`, 비용률 기준일 `2026-05-26`, `nav_premium_discount.status=collected`, NAV `745.571145`, closing price `745.64`, premium/discount `0.0`, NAV 기준일 `2026-05-22`, `tracking_error.status=tracking_difference_collected`, `metric_type=tracking_difference`, true tracking error value `null`, one-year tracking difference `-0.0021`, fund NAV return `0.3084`, benchmark return `0.3105`, benchmark `S&P 500 Index`, tracking difference 기준일 `2026-04-30`, `order_boundary=read_only_no_order`를 반환한다. EC2 import `run_id=1592`, `fund_metric_snapshot_ids=[6,7,8,9,10,11,12,13]`이고 `/stocks/SPY`와 `/recommendations/recommendation-157` route smoke는 `추적오차/추적차이`, `추적차이 원천 열기`, `기간 1 Year`, `S&P 500 Index`, `NAV 수익률 30.8%`, `벤치마크 31.1%`, `NAV 괴리`, `주문 경계` 문구를 확인했다. 다음 작업은 추천 weight 변경 전 outcome/calibration 표본을 확장하는 `recommendation-outcome-calibration-sample-expansion-v1`이다.
- 최신 recommendation outcome cadence action 증거는 EC2 commit `bf44aae`이다. `/api/data-health`는 `recommendation_outcome_maturity.status=not_due`, `next_due_date=2026-06-20`, `next_due_count=19`, `cadence_action.status=wait_until_next_due_date`, `cadence_action.action_type=wait`, `should_run_now=false`, `should_wait=true`, `wait_until=2026-06-20`, command `stockanalysis-operations recommendation-outcome-calibration-sample-expansion-run --env-file <ENV> --as-of-date 2026-06-20 --execute`, `blocks_weight_review=true`, `automatic_weight_change_allowed=false`를 반환한다. `/data-health`는 `실행 액션`, `다음 측정일까지 대기`, `성과 측정창`, `다음 측정일`을 노출한다.
- 최신 `professional-source-gap-prioritization-v1` 증거는 EC2 commit `44012fb`이다. `/api/data-health`는 `professional_source_gap_prioritization.status=source_blockers_present`, `gap_count=3`, `source_blocker_count=1`, `fund_not_applicable_count=1`, top symbols `EROK:source_blocker`, `GOOG:coverage_gap`, `SPY:fund_not_applicable`, `recommendation_scoring_mutated=false`, `automatic_order_allowed=false`를 반환한다. `/data-health`는 `전문 분석 소스 공백`, `원천 차단 종목 있음`, `EROK`, `SPY`, `기업 재무 모델 비적용`을 렌더링한다. 다음 작업은 `professional-source-gap-remediation-decision-v1`로, `EROK`의 free-public-data remediation 가능 여부를 먼저 판정하고 불가능하면 합성 재무 없이 다음 deterministic coverage gap으로 이동한다.

## Definition Of Done

작업은 아래가 모두 충족될 때만 완료다.

- 요청한 변화가 실제로 존재한다
- 필요한 검증이 수행되었다
- 남은 위험과 미검증 영역이 적혀 있다
- 현재 task directory가 다음 사람이 이어받을 수 있을 만큼 갱신되어 있다
- 아키텍처 또는 규칙 변경이면 관련 설계 문서와 task handoff가 함께 갱신되어 있다
