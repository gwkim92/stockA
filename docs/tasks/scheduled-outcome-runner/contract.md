# Task Contract

## Task

- 이름: scheduled-outcome-runner
- 요청: 추천 batch별 due horizon을 자동 탐색해 장기 outcome runner를 실행한다.
- 담당: Codex
- 날짜: 2026-04-27

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `performance-outcome-schedule-bootstrap` CLI가 due date와 horizon days를 받아 outcome이 아직 비어 있는 recommendation batch/horizon을 찾아 `performance.recommendation_outcome`, `performance.thesis_outcome`을 생성한다.

## Why

- 프로젝트는 중장기/장기 추천 성과를 지속 추적해야 한다. 매번 measurement date를 수동 지정하면 운영 자동화가 불가능하고, 누락된 horizon을 체계적으로 관리하기 어렵다.

## Scope

- 포함:
  - due outcome candidate lookup
  - default horizon days `(30, 90, 180, 365)`
  - repeatable custom `--horizon-day`
  - schedule parent pipeline run
  - existing outcome runner 재사용
  - candidate-level failure summary
  - CLI, unit tests, Docker integration verification
  - docs/task handoff 갱신
- 제외:
  - OS cron 또는 app automation 생성
  - 실거래 PnL
  - price data 자동 backfill scheduling
  - recommendation score 변경
  - thesis generation 변경
  - portfolio attribution 변경

## Mutable Surface

- 수정 가능한 파일:
  - `README.md`
  - `docs/performance-outcome-bootstrap.md`
  - `docs/plans/2026-04-27-scheduled-outcome-runner.md`
  - `docs/scheduled-outcome-runner.md`
  - `docs/tasks/scheduled-outcome-runner/`
  - `docs/verification-plan.md`
  - `scripts/verify_scheduled_outcome_runner.sh`
  - `src/stockanalysis/ingest/cli.py`
  - `src/stockanalysis/performance/outcome.py`
  - `tests/test_ingest_cli.py`
  - `tests/test_performance_outcome_bootstrap.py`
- 수정 금지 파일:
  - recommendation score formula
  - thesis generation rule
  - portfolio attribution methodology
  - DB schema unless schedule state cannot be represented by existing tables
- 검증에 사용할 명령:
  - `python3 -m compileall src tests`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `bash -n scripts/verify_scheduled_outcome_runner.sh`
  - `bash scripts/verify_scheduled_outcome_runner.sh`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo /Users/woody/ai/stockanalysis --task scheduled-outcome-runner`
  - `rg -n "\[[A-Z0-9_]+\]" AGENTS.md docs -S`

## Deliverables

- 필수 결과물:
  - `performance-outcome-schedule-bootstrap` CLI
  - due candidate lookup
  - schedule runner tests
  - Docker verify script
  - schedule runner docs
  - task contract/plan/handoff/review

## Completion Criteria

- [x] default horizon days가 `(30, 90, 180, 365)`로 resolve된다.
- [x] custom horizon days가 dedupe/sort되고 invalid value를 거부한다.
- [x] candidate lookup이 outcome이 비어 있는 due batch/horizon만 반환한다.
- [x] schedule runner가 기존 outcome runner를 재사용한다.
- [x] candidate 실패가 summary에 남고 parent run은 failed로 표시된다.
- [x] Docker verify가 schedule CLI로 AAPL outcome 2건을 생성한다.
- [x] docs와 handoff가 갱신된다.
- [x] 하네스 검증이 통과한다.

## Verification Plan

- 자동 검증: compileall, unittest, shell syntax, Docker integration verify, harness verify, placeholder 검색
- 수동 검증: `docs/scheduled-outcome-runner.md`에서 schedule boundary와 실제 cron 미포함 범위가 명확한지 확인
- 어떤 증거가 있어야 완료로 간주하는가: Docker Postgres에서 schedule CLI가 2024-11-01 batch의 3일/31일 outcome 2건을 만들고, latest `performance_outcome_schedule_bootstrap` run status `succeeded`다.

## Risks

- due date는 calendar day 기준이다. 실제 거래일 보정은 기존 price lookup의 latest-on-or-before rule에 맡긴다.
- schedule runner는 price backfill을 하지 않는다. 가격이 없으면 candidate-level failure로 남는다.
- 이 작업은 runner이며 OS-level recurring automation은 아니다.
