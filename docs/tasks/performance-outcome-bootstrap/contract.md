# Task Contract

이 문서는 멀티파일 작업, 위험 작업, 세션을 넘길 작업을 시작하기 전에 채운다.

## Task

- 이름: performance-outcome-bootstrap
- 요청: recommendation과 thesis의 사후 가격 성과를 performance schema에 저장한다.
- 담당: Codex
- 날짜: 2026-04-26

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `performance-outcome-bootstrap` CLI가 recommendation batch와 measurement end date를 받아 `performance.recommendation_outcome`과 `performance.thesis_outcome` rows를 저장한다.

## Why

- 추천, thesis, review, portfolio review까지 생성돼도 성과가 저장되지 않으면 판단 품질을 검증할 수 없다. 성과 outcome이 있어야 어떤 추천/논리/사이클 판단이 실제로 맞았는지, 실패했는지, 개선해야 할 점이 무엇인지 추적할 수 있다.

## Inputs

- 관련 코드:
  - `src/stockanalysis/signal/recommendation.py`
  - `src/stockanalysis/signal/thesis.py`
  - `src/stockanalysis/ingest/market/price.py`
  - `src/stockanalysis/ingest/cli.py`
- 관련 schema:
  - `signal.recommendation_batch`
  - `signal.recommendation`
  - `signal.investment_thesis`
  - `market.daily_price_bar`
  - `performance.recommendation_outcome`
  - `performance.thesis_outcome`
- 이전 결정:
  - 투자 추천 로직은 설명 가능한 규칙과 검증 가능한 평가 체계를 먼저 갖춘 뒤 고도화한다.
  - 추천 또는 보유 판단은 당시 입력 데이터, 점수, thesis, 무효화 조건을 함께 저장한다.

## Scope

- 포함:
  - performance outcome migration
  - recommendation outcome computation
  - thesis outcome computation
  - absolute return, optional benchmark return, alpha, max drawdown
  - CLI, tests, Docker verify, docs
- 제외:
  - portfolio-level attribution
  - sector/theme attribution
  - live benchmark source adapter
  - AI grading
  - real trade PnL

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `db/migrations/0010_performance_outcome.sql`
  - `docs/db-schema-design.md`
  - `docs/performance-outcome-bootstrap.md`
  - `docs/plans/2026-04-26-performance-outcome-bootstrap.md`
  - `docs/tasks/performance-outcome-bootstrap/`
  - `docs/verification-plan.md`
  - `scripts/verify_performance_outcome_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/performance/`
  - `tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json`
  - `tests/test_ingest_cli.py`
  - `tests/test_performance_outcome_bootstrap.py`
- 수정 금지 파일:
  - recommendation score formula
  - thesis generation rule
  - portfolio review action rule
  - broker/trade execution path
  - benchmark policy beyond optional instrument price lookup
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_performance_outcome_bootstrap.sh`
  - `bash scripts/verify_performance_outcome_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task performance-outcome-bootstrap`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `db/migrations/0010_performance_outcome.sql`
  - `src/stockanalysis/performance/outcome.py`
  - `tests/test_performance_outcome_bootstrap.py`
  - `tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json`
  - `scripts/verify_performance_outcome_bootstrap.sh`
  - `docs/performance-outcome-bootstrap.md`
  - `docs/tasks/performance-outcome-bootstrap/contract.md`
  - `docs/tasks/performance-outcome-bootstrap/plan.md`
  - `docs/tasks/performance-outcome-bootstrap/handoff.md`
  - `docs/tasks/performance-outcome-bootstrap/review.md`

## Completion Criteria

- [x] 요청한 산출물이 기대 위치에 존재한다
- [x] 완료를 증명할 검증 계획이 있다
- [x] 범위 밖 변경이 없다
- [x] 남은 위험과 미확정 사항이 적혀 있다
- [x] 다음 단계가 분명하다
- [x] `performance.recommendation_outcome`과 `performance.thesis_outcome` table이 실제 migration에 존재한다
- [x] `performance-outcome-bootstrap` CLI가 outcome rows를 저장한다
- [x] benchmark가 없을 때도 absolute return outcome이 저장된다
- [x] 성과 측정이 추천/보유 판단과 분리되어 있음이 문서화되어 있다

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/performance-outcome-bootstrap.md`에서 outcome formula, boundary, next step이 명확한지 확인
- 브라우저, 로그, metric 검증: 현재는 CLI/DB 단계라 브라우저 검증 없음
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 AAPL recommendation outcome 1건, thesis outcome 1건, absolute return `0.010000`, latest `performance_outcome_bootstrap` pipeline run status가 `succeeded`다.

## Rollback Or Fallback

- 검증이 실패했을 때 되돌리거나 끌 수 있는 방법: `0010_performance_outcome.sql`, performance outcome runner, CLI command, verify script, docs만 제거하면 이전 portfolio review 상태로 복귀한다.

## Open Questions

- 질문: benchmark price가 없으면 어떻게 할지
- 답이 없을 때 적용할 임시 가정: benchmark_return_pct와 alpha_pct는 null로 두고 absolute_return_pct는 저장한다.

- 질문: 여러 measurement horizon을 한 recommendation에 저장할지
- 답이 없을 때 적용할 임시 가정: `recommendation_id + measurement_end_date` unique로 여러 측정일을 허용한다.
