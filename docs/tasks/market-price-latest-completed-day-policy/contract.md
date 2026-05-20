# Task Contract

## Task

- 이름: market-price-latest-completed-day-policy
- 요청: `market-price-daily-run`의 기본 freshness target을 scheduler run date가 아니라 최신 완료 미국 거래일로 계산하게 한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 명시 `--freshness-date`나 env override가 없을 때 `market-price-daily-run`은 미국 동부 시간대 기준 최신 완료 거래일을 freshness target으로 사용하고, 반복 실행이 같은 날짜 데이터에 대해 provider call을 낭비하지 않는다.

## Why

- 2026-05-19 KST 오전에는 미국 시장 최신 완료 거래일이 2026-05-18이다.
- 단순히 local/UTC run date를 freshness target으로 쓰면 2026-05-19 데이터를 기대하게 되어 같은 2026-05-18 bar를 다시 호출할 위험이 있다.
- scheduler activation 전에는 거래일 기준 freshness policy가 먼저 고정되어야 한다.

## Scope

- `market-price-daily-run` 기본 freshness policy를 `latest_completed_us_market_day`로 바꾼다.
- 명시 `--freshness-date`와 `DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_FRESHNESS_DATE`는 우선권을 유지한다.
- 주말은 자동 제외하고, 휴장일은 repo-outside env `DATA_OPERATIONS_SCHEDULER_MARKET_PRICE_NON_TRADING_DATES`로 제외한다.
- 실행 summary에 freshness policy/source/target을 남긴다.
- unit tests, CLI docs/runbook, task docs를 갱신한다.

## Boundaries

- 외부 holiday/calendar API를 추가하지 않는다.
- 실제 `launchctl bootstrap`, `kickstart`, `~/Library/LaunchAgents` 쓰기는 하지 않는다.
- `.env` 또는 provider API key 값을 출력하거나 repo에 저장하지 않는다.
- DB schema, scoring, benchmark, evaluation split, broker/order flow는 바꾸지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/market_price_free_backfill.py`
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/cadence.py`
  - `tests/test_market_price_free_backfill.py`
  - `tests/test_data_operations_cli.py`
  - `tests/test_data_operations_cadence.py`
  - `docs/data-operations-scheduler-activation-runbook.md`
  - `docs/tasks/market-price-latest-completed-day-policy/*`
  - `docs/tasks/local-live-mvp-runtime/handoff.md`
  - `docs/tasks/local-live-mvp-runtime/review.md`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_market_price_free_backfill tests.test_data_operations_cli tests.test_data_operations_cadence`
  - scheduler-free dry run or zero-call run proving target `2026-05-18` skips fresh symbols
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task market-price-latest-completed-day-policy`
  - `git diff --check`

## Done Criteria

- [x] default daily freshness target uses latest completed US market day.
- [x] explicit argument/env override still wins.
- [x] weekend and configured non-trading dates are handled.
- [x] summary exposes policy/source without secrets.
- [x] docs and handoff explain the scheduler activation implication.
