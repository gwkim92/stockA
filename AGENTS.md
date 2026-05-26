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
- 현재 고정된 immediate next task는 `portfolio-risk-budget-benchmark-composition-v1`이다. 기존 `portfolio-risk-budget-policy-v2`는 화면/API DTO 기준으로 완료되었고, `portfolio-risk-budget-guardrail-run`은 EC2에서 `run_id=976`, `eval_run_id=19`, `risk_gate_decision=blocked_by_risk_budget_review`로 통과했다. `portfolio-risk-budget-paper-validation-integration`은 EC2에서 `paper_validation_run_id=12`, `portfolio_risk_budget_guardrail.eval_run_id=19`, `validation_status=failed`, `conflict_count=0`, `submitted_to_broker_count=0`으로 통과했고, risk budget blocker가 paper validation blocked reasons에 반영된다. `portfolio-risk-budget-frontend-guardrail-visibility`는 EC2 commit `b494474`에서 `/paper-trading`, `/trading-readiness`, `/portfolio/coverage`, `/api/trading/readiness` route/API smoke가 통과했고 persisted guardrail blocker를 사용자 화면에 노출한다. `professional-coverage-expansion-for-active-recommendations`는 EC2에서 active recommendation complete professional coverage를 `30/36 = 0.833333`까지 올렸고, `recommendation-outcome-backfill-run`은 가격 기반 recommendation outcome `55`개와 thesis outcome `43`개를 생성했다. 최신 `recommendation-quality-eval-run`은 `run_id=890`, `eval_run_id=13`, `quality_status=ready_for_weight_review`, `sample_status=sufficient_sample`이다. `paper-safety-interlock-policy`는 EC2에서 `run_id=973`, `audit_eval_run_id=16`, `decision=ready_for_manual_weight_review`로 통과했다. `manual-weight-review-calibration-report`는 EC2에서 `run_id=975`, `report_eval_run_id=18`, `decision=manual_review_allowed_keep_weights_collect_more_evidence`로 통과했고, `eligible_for_manual_pilot_review_count=0`, `keep_zero_or_do_not_increase_count=12`를 기록했다. 추천 weight 변경은 별도 승인된 pilot-weight task 전까지 금지한다. 다음 작업은 무료 benchmark composition source 또는 명시적 수동 benchmark composition seed를 추가해 현재 `insufficient_benchmark_composition`인 drift를 실제 측정 가능하게 만드는 것이다. EC2에서는 FastAPI/Next.js와 profile별 `systemd` scheduler가 운영 후보로 동작 중이며, `stockanalysis-mvp-20260520`의 현재 public IPv4는 `34.206.72.213`이다. Codex OAuth는 EC2 재로그인 후 실제 `cycle-community-ai-summary-v2-run --provider codex_oauth --execute` smoke가 `run_id=712`, `invocation_id=983`, `failed_summary_count=0`으로 성공했다. 새 data operations 작업은 shell orchestration을 늘리지 말고 `stockanalysis-operations` backend CLI/service boundary를 우선 사용한다. 추천 scoring weight와 실거래 자동화는 별도 승인 전까지 범위 밖이다.

## Definition Of Done

작업은 아래가 모두 충족될 때만 완료다.

- 요청한 변화가 실제로 존재한다
- 필요한 검증이 수행되었다
- 남은 위험과 미검증 영역이 적혀 있다
- 현재 task directory가 다음 사람이 이어받을 수 있을 만큼 갱신되어 있다
- 아키텍처 또는 규칙 변경이면 관련 설계 문서와 task handoff가 함께 갱신되어 있다
