# Task Contract

## Task

- 이름: market-price-scheduler-freshness-defaults
- 요청: recurring market-price job이 Twelve Data 확장 watchlist와 freshness skip을 기본 경계로 쓰게 만든다.
- 담당: Codex
- 날짜: 2026-05-18

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `market-price-daily` scheduler command는 repo-outside env의 watchlist/ledger/provider 설정을 읽고, 기본적으로 `skip_if_fresh`와 scheduler run date 기반 freshness date를 사용한다.

## Why

- 현재 local MVP는 수동 실행으로 25개 종목 가격을 적재했고 freshness skip도 검증했다.
- 그러나 cadence/runbook 기본값은 아직 Alpha Vantage 25/day와 `<CSV>/<JSON>` placeholder 중심이라 recurring scheduler에 그대로 쓰면 중복 호출과 잘못된 provider default가 발생할 수 있다.

## Scope

- operations CLI에 scheduler-friendly `market-price-daily-run` boundary를 추가한다.
- data operations env readiness가 market price provider, watchlist, budget ledger를 검증하게 한다.
- `market-price-daily` cadence template을 Twelve Data/free-provider freshness policy로 갱신한다.
- scheduler wrapper가 `DATA_OPERATIONS_SCHEDULER_RUN_DATE`를 child command에 export하게 한다.
- repo-outside local env에 expanded watchlist 경로와 market-price scheduler defaults를 추가한다.
- runbook/handoff 문서와 tests를 갱신한다.

## Boundaries

- 실제 `launchctl bootstrap`, `kickstart`, `~/Library/LaunchAgents` 쓰기는 하지 않는다.
- provider key 값은 출력하거나 repo에 저장하지 않는다.
- DB schema, scoring, benchmark, evaluation split, broker/order flow는 바꾸지 않는다.

## Mutable Surface

- 수정 가능한 파일:
  - `src/stockanalysis/operations/cadence.py`
  - `src/stockanalysis/operations/env_readiness.py`
  - `src/stockanalysis/operations/cli.py`
  - `scripts/run_data_operations_scheduler_job.sh`
  - `docs/data-operations-scheduler-activation-runbook.md`
  - tests
  - task docs
  - repo-outside `/private/tmp/stockanalysis-runtime/data-operations.real.env`

## Verification Commands

- 검증에 사용할 명령:
  - `PYTHONPATH=src /private/tmp/stockanalysis-runtime/venv/bin/python -m unittest tests.test_data_operations_cadence tests.test_data_operations_env_readiness tests.test_data_operations_cli tests.test_data_operations_scheduler_boundary`
  - `PYTHON_BIN=/private/tmp/stockanalysis-runtime/venv/bin/python scripts/check_data_operations_runtime_env.sh --env-file /private/tmp/stockanalysis-runtime/data-operations.real.env`
  - scheduler boundary preflight for `market-price-daily`
  - scheduler boundary live local run with all symbols fresh and `provider_request_count=0`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task market-price-scheduler-freshness-defaults`
  - `git diff --check`

## Done Criteria

- [x] `market-price-daily-run` reads watchlist/ledger/provider from env.
- [x] market price provider readiness validates Twelve Data key, watchlist path, and ledger path without secret values.
- [x] scheduler child process receives `DATA_OPERATIONS_SCHEDULER_RUN_DATE`.
- [x] cadence/runbook defaults mention freshness skip and market-price env policy.
- [x] local scheduler boundary run consumes zero provider calls when all symbols are fresh.
