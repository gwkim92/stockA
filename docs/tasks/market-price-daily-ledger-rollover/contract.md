# Task Contract

## Task

- 이름: market-price-daily-ledger-rollover
- 요청: 2026-05-19 local live MVP에서 Twelve Data market-price daily run을 scheduler 없이 수동 실행해 provider budget `day_missing` 상태를 해소한다.
- 담당: Codex
- 날짜: 2026-05-19

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: `/api/data-health`의 provider budget은 2026-05-19 기준 ledger entry를 읽고, `market-price-daily` run artifact는 최신 완료 미국 거래일 target을 명시한다.

## Why

- `/data-health`는 전체 운영 상태가 `healthy`지만 날짜가 2026-05-19로 넘어가며 provider budget이 `day_missing`으로 표시된다.
- 단순 run date `2026-05-19`를 freshness target으로 쓰면 미국 시장 최신 완료 거래일인 `2026-05-18` 데이터를 받아도 반복 호출 위험이 있다.
- scheduler activation 전에는 수동 artifact runner로 실행 증거를 쌓는 것이 안전하다.

## Scope

- live `/api/data-health` provider budget 상태를 before evidence로 기록한다.
- repo-outside env readiness를 확인한다.
- `stockanalysis-operations market-price-daily-run`을 scheduler 없이 실행한다.
- budget date는 `2026-05-19`, freshness target은 `2026-05-18`로 둔다.
- 실행 후 `/api/data-health`, DB latest price dates, artifact stdout을 확인한다.
- task handoff/review와 local live MVP handoff를 갱신한다.

## Boundaries

- 실제 `launchctl bootstrap`, `kickstart`, `~/Library/LaunchAgents` 쓰기는 하지 않는다.
- `.env` 또는 provider API key 값을 출력하거나 repo에 저장하지 않는다.
- DB schema, scoring, benchmark, evaluation split, broker/order flow는 바꾸지 않는다.
- product orchestration을 새 shell script로 늘리지 않고 `stockanalysis-operations` backend CLI/service boundary를 사용한다.

## Mutable Surface

- 수정 가능한 파일:
  - `docs/tasks/market-price-daily-ledger-rollover/*`
  - `docs/tasks/local-live-mvp-runtime/handoff.md`
  - `docs/tasks/local-live-mvp-runtime/review.md`
- repo-outside runtime artifact:
  - `/private/tmp/stockanalysis-runtime/artifacts/*`
  - `/private/tmp/stockanalysis-runtime/twelve-data-budget-ledger.json`

## Verification Commands

- 검증에 사용할 명령:
  - authorized `/api/data-health` live query before/after
  - `stockanalysis-operations market-price-daily-run --budget-date 2026-05-19 --freshness-date 2026-05-18`
  - DB latest price date sample for the expanded watchlist
  - browser smoke for `/data-health`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/venv/bin/python -m awh verify --repo . --task market-price-daily-ledger-rollover`
  - `git diff --check`

## Done Criteria

- [x] before/after provider budget evidence가 기록된다.
- [x] market-price daily run artifact가 남는다.
- [x] 실행 결과가 provider request count, success/fresh-skip/failure counts를 명확히 보여준다.
- [x] `/data-health`가 2026-05-19 provider budget ledger 상태를 표시한다.
- [x] host scheduler mutation이 없었다는 사실이 기록된다.
