# Task Contract

## Task

- 이름: long-horizon-outcome-runner
- 요청: 하나의 recommendation batch에 대해 여러 measurement horizon 성과를 저장한다.
- 담당: Codex
- 날짜: 2026-04-27

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `performance-outcome-batch-bootstrap` CLI가 여러 measurement date 또는 horizon day를 받아 `performance.recommendation_outcome`, `performance.thesis_outcome`에 여러 outcome rows를 저장한다.

## Why

- 프로젝트는 중장기/장기 투자 판단을 목표로 한다. 단일 단기 측정일만 저장하면 추천 품질의 시간 경과와 thesis 지속성을 검증할 수 없다.

## Scope

- 포함:
  - multiple measurement date resolver
  - batch outcome runner
  - batch CLI
  - long horizon price fixture
  - unit tests and Docker integration verification
  - docs/task handoff 갱신
- 제외:
  - schema 변경
  - recommendation score 변경
  - thesis generation 변경
  - 실거래 PnL
  - portfolio attribution
  - scheduler/cron automation

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/performance-outcome-bootstrap.md`
  - `docs/plans/2026-04-27-long-horizon-outcome-runner.md`
  - `docs/tasks/long-horizon-outcome-runner/`
  - `docs/verification-plan.md`
  - `scripts/verify_performance_outcome_bootstrap.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/performance/outcome.py`
  - `tests/fixtures/alpha_vantage_daily_adjusted_AAPL_outcome.json`
  - `tests/fixtures/alpha_vantage_daily_adjusted_SPY.json`
  - `tests/test_ingest_cli.py`
  - `tests/test_performance_outcome_bootstrap.py`
- 수정 금지 파일:
  - recommendation score formula
  - thesis generation rule
  - portfolio review action rule
  - DB schema unless current unique key cannot support multiple horizons
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_performance_outcome_bootstrap.sh`
  - `bash scripts/verify_performance_outcome_bootstrap.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task long-horizon-outcome-runner`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `performance-outcome-batch-bootstrap` CLI
  - batch runner tests
  - long horizon AAPL/SPY fixture values
  - Docker verify with two measurement dates
  - task contract/plan/handoff/review

## Completion Criteria

- [x] batch runner가 여러 measurement date를 처리한다.
- [x] horizon day input이 measurement date로 변환된다.
- [x] duplicate measurement dates are deduplicated.
- [x] Docker verify가 short/long horizon outcome 2건을 확인한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/performance-outcome-bootstrap.md`에서 batch CLI와 long horizon boundary가 명확한지 확인
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 AAPL recommendation outcome 2건, thesis outcome 2건, 2024-11-04 alpha `0.005000`, 2024-12-02 alpha `0.060000`, latest `performance_outcome_bootstrap` run status `succeeded`다.

## Risks

- horizon day는 calendar day 기준이다. trading day 보정은 price lookup의 latest-on-or-before rule에 맡긴다.
- fixture는 31일 horizon이라 실제 장기 투자 검증은 아니다. 구조 검증이 목적이다.
