# Task Contract

## Task

- 이름: recommendation-outcome-backfill
- 요청: 추천 품질 평가에 필요한 outcome 데이터를 실제 가격 데이터 기반으로 쌓거나 재현 가능하게 생성한다.
- 담당: Codex
- 날짜: 2026-05-24

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `stockanalysis-operations recommendation-outcome-backfill-run --due-on-date YYYY-MM-DD --horizon-day 30`가 due recommendation batch를 찾고, `--execute`일 때만 `performance.recommendation_outcome`, `performance.thesis_outcome`, `ops.pipeline_run`에 가격 기반 outcome을 기록한다.

## Scope

- 포함:
  - 기존 `performance.outcome` schedule bootstrap 재사용
  - operations CLI wrapper 추가
  - dry-run/preview summary와 execute summary 분리
  - decision-daily에서 recommendation quality eval 전에 30일 outcome backfill 실행
  - cadence registry에 daily backfill job 노출
  - unit/CLI/orchestrator/cadence tests
- 제외:
  - synthetic return 생성
  - 추천 산식/weight 변경
  - DB schema 변경
  - broker/order submit
  - Codex OAuth 호출

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/recommendation_outcome_backfill.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/operating_data_orchestrator.py`
  - `src/stockanalysis/operations/cadence.py`
  - `tests/test_recommendation_outcome_backfill.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_operating_data_orchestrator.py`
  - `tests/test_data_operations_cadence.py`
  - `docs/tasks/recommendation-outcome-backfill/*`
- 수정 금지 파일:
  - 추천 scoring weight
  - performance outcome schema
  - broker/order submit path
  - `.env` secret values

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_recommendation_outcome_backfill tests.test_data_operations_cli tests.test_operating_data_orchestrator tests.test_data_operations_cadence`
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m compileall -q src tests`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /opt/homebrew/bin/python3.13 -m awh verify --repo . --task recommendation-outcome-backfill`

## Done Criteria

- 백필은 `market.daily_price_bar` 기반 outcome만 생성한다.
- 가격 데이터 또는 due candidate가 없으면 no-op/preview로 보고하고 가짜 outcome을 만들지 않는다.
- `decision-daily`는 recommendation quality eval 전에 30일 outcome backfill을 실행한다.
- 기존 monthly performance outcome 경로는 operations CLI boundary를 사용한다.
